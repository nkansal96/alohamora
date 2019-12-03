""" Implements the logic to read the file store, generate the server config, and start the servers """

import contextlib
import os
import subprocess
import sys
import tempfile
import gzip
from typing import Optional
from urllib.parse import urlparse
from io import BytesIO

from bs4 import BeautifulSoup

from blaze.action import Policy
from blaze.logger import logger

from blaze.mahimahi.server.dns import DNSServer
from blaze.mahimahi.server.filestore import FileStore
from blaze.mahimahi.server.interfaces import Interfaces
from blaze.mahimahi.server.nginx_config import Config


def prepend_javascript_snippet(input_string: str):
    """
    gets in an html representation of the website
    converts into a beautifulsoup object
    adds a javascript tag to fetch critical requests
    converts back into string and returns
    """
    soup = BeautifulSoup(input_string, "html.parser")
    if soup.html is None:
        return str(soup)
    dir_name = "/opt/blaze/blaze/mahimahi/server/injected-javascript"
    for file_name in ["find-in-viewport.js", "interceptor.js"]:
        curr_file = os.path.join(dir_name, file_name)
        with open(curr_file) as f:
            file_contents = f.read()
            script_tag = soup.new_tag("script")
            script_tag["type"] = "application/javascript"
            script_tag.string = file_contents
            soup.html.insert(0, script_tag)
    return str(soup)


def inject_extract_critical_requests_javascript(file):
    """
    tries to inject the two js files in the given file.
    throws exception if an error happens
    returns body as string after injection
    """
    uncompressed_body = file.body
    gzipped_file = False
    if (
        file.headers is not None
        and file.headers.get("content-encoding") is not None
        and "gzip" in file.headers.get("content-encoding")
    ):
        gzipped_file = True
        uncompressed_body = gzip.GzipFile(fileobj=BytesIO(uncompressed_body)).read()
    uncompressed_body = prepend_javascript_snippet(uncompressed_body)
    if gzipped_file:
        out = BytesIO()
        with gzip.GzipFile(fileobj=out, mode="wb") as f:
            f.write(uncompressed_body.encode())
        file.body = out.getvalue()
    else:
        file.body = uncompressed_body
    return file.body


@contextlib.contextmanager
def start_server(
    replay_dir: str,
    cert_path: Optional[str] = None,
    key_path: Optional[str] = None,
    policy: Optional[Policy] = None,
    extract_critical_requests: Optional[bool] = False,
):
    """
    Reads the given replay directory and sets up the NGINX server to replay it. This function also
    creates the DNS servers, Interfaces, and writes all necessary temporary files.

    :param replay_dir: The directory to replay (should be mahimahi-recorded)
    :param cert_path: The path to the SSL certificate for the HTTP/2 NGINX server
    :param key_path: The path to the SSL key for the HTTP/2 NGINX server
    :param policy: The path to the push/preload policy to use for the server
    """
    log = logger.with_namespace("replay_server")
    push_policy = policy.as_dict["push"] if policy else {}
    preload_policy = policy.as_dict["preload"] if policy else {}

    # Load the file store into memory
    if not os.path.isdir(replay_dir):
        raise NotADirectoryError(f"{replay_dir} is not a directory")
    filestore = FileStore(replay_dir)

    # Create host-ip mapping
    hosts = filestore.hosts
    interfaces = Interfaces(hosts)
    host_ip_map = interfaces.mapping

    # Save files and create nginx configuration
    config = Config()
    with tempfile.TemporaryDirectory() as file_dir:
        log.debug("storing temporary files in", file_dir=file_dir)

        for host, files in filestore.files_by_host.items():
            log.info("creating host", host=host, address=host_ip_map[host])
            uris_served = set()

            # Create a server block for this host
            server = config.http_block.add_server(
                server_name=host, server_addr=host_ip_map[host], cert_path=cert_path, key_path=key_path, root=file_dir
            )

            for file in files:
                # Handles the case where we may have duplicate URIs for a single host
                # or where URIs in nginx cannot be too long
                if file.uri in uris_served or len(file.uri) > 3600 or len(file.headers.get("location", "")) > 3600:
                    continue

                uris_served.add(file.uri)
                log.debug(
                    "serve",
                    file_name=file.file_name,
                    status=file.status,
                    method=file.method,
                    uri=file.uri,
                    host=file.host,
                )

                # Create entry for this resource
                if file.status < 300:
                    loc = server.add_location_block(
                        uri=file.uri, file_name=file.file_name, content_type=file.headers.get("content-type", None)
                    )
                elif "location" in file.headers:
                    loc = server.add_location_block(uri=file.uri, redirect_uri=file.headers["location"])
                else:
                    log.warn("skipping", file_name=file.file_name, method=file.method, uri=file.uri, host=file.host)
                    continue

                backup_file_body = file.body
                try:
                    if extract_critical_requests and "text/html" in file.headers.get("content-type", ""):
                        file.body = inject_extract_critical_requests_javascript(file)
                    file_path = os.path.join(file_dir, file.file_name)
                    with open(os.open(file_path, os.O_CREAT | os.O_WRONLY, 0o644), "wb") as f:
                        f.write(file.body)
                except TypeError as e:
                    file_path = os.path.join(file_dir, file.file_name)
                    with open(os.open(file_path, os.O_CREAT | os.O_WRONLY, 0o644), mode="w", encoding="utf8") as f:
                        f.write(file.body)
                except UnicodeEncodeError as e:
                    # file.body somehow because corrupted.
                    # this messes up the encoding
                    # Save the file's original body to file
                    # this happens if a file is a bytestream but does not have gzip header or vice versa
                    log.warn("unable to inject critical for file ", uri=file.uri, error=e)
                    file.body = backup_file_body
                    file_path = os.path.join(file_dir, file.file_name)
                    with open(os.open(file_path, os.O_CREAT | os.O_WRONLY, 0o644), "wb") as f:
                        f.write(file.body)

                # Add headers
                for key, value in file.headers.items():
                    loc.add_header(key, value)

                # Look up push and preload policy
                full_source = f"https://{file.host}{file.uri}"
                push_res_list = push_policy.get(full_source, push_policy.get(full_source + "/", []))
                preload_res_list = preload_policy.get(full_source, preload_policy.get(full_source + "/", []))

                for res in push_res_list:
                    path = urlparse(res["url"]).path
                    log.debug("create push rule", source=file.uri, push=path)
                    loc.add_push(path)
                for res in preload_res_list:
                    log.debug("create preload rule", source=file.uri, preload=res["url"], type=res["type"])
                    loc.add_preload(res["url"], res["type"])

        # Save the nginx configuration
        conf_file = os.path.join(file_dir, "nginx.conf")
        log.debug("writing nginx config", conf_file=conf_file)
        with open(conf_file, "w") as f:
            f.write(str(config))

        # Create the interfaces, start the DNS server, and start the NGINX server
        with interfaces:
            with DNSServer(host_ip_map):
                # If wait lasts for more than 0.5 seconds, a TimeoutError will be raised, which is okay since it
                # means that nginx is running successfully. If it finishes sooner, it means it crashed and
                # we should raise an exception
                try:
                    proc = subprocess.Popen(
                        ["/usr/local/openresty/nginx/sbin/nginx", "-c", conf_file], stdout=sys.stderr, stderr=sys.stderr
                    )
                    proc.wait(0.5)
                    raise RuntimeError("nginx exited unsuccessfully")
                except subprocess.TimeoutExpired:
                    yield
                finally:
                    proc.terminate()
