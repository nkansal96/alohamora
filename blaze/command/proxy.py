""" Implements the commands for converting a push policy to an nginx configuration """
from pathlib import Path
import json
import sys
import os
from typing import List
from urllib.parse import urlparse, urlunparse

from blaze.action import Policy
from blaze.config.environment import EnvironmentConfig, PushGroup
from blaze.mahimahi.server.nginx_config_without_lua import Config
from blaze.logger import logger as log

from . import command

@command.argument("--policy", help="The file path to a JSON-formatted push/preload policy to convert to nginx config", required=True)
@command.argument("--output", help="The filepath  to save the prepared nginx config", required=True)
@command.argument("--hostname", help="The hostname of the website for which this push policy is applicable. Do not include the protocol. Eg. www.walgreens.com", required=True)
@command.command
def convert(args):
    """
    Convert a push policy to an nginx proxy configuration file. 
    """
    log.debug("reading policy", push_policy=args.policy)
    with open(args.policy, "r") as policy_file:
        policy_dict = json.load(policy_file)
    policy = Policy.from_dict(policy_dict)
    
    config = Config()
    server_block = config.add_server(server_name=args.hostname,server_addr="127.0.0.1")

    for ptype, policy_obj in policy_dict.items():
        if ptype == "push" or ptype == "preload":
            for (source, deps) in policy_obj.items():
                location_block = server_block.add_location_block(uri=source)
                log.debug("source is ", url=source)
                for obj in deps:
                    if ptype == "push":
                        location_block.add_push(uri=obj["url"])
                        log.debug("child is ", url=obj["url"])
                    elif ptype == "preload":
                        location_block.add_preload(uri=obj["url"], as_type=obj["type"])
                        log.debug("child is ", url=obj["url"])
    log.debug("final config is ", nginx_config=config)
    with open(args.output, "w") as f:
        f.write(str(config))


@command.argument("--input_folder", help="The file path to a JSON-formatted push/preload policy to convert to nginx config", required=True)
@command.argument("--output_folder", help="The filepath  to save the prepared nginx config", required=True)
@command.command
def convert_folder(args):
    """
    Takes in a folder that contains a number of push policy files. 
    Each file should be json formatted with a push and preload fields. 
    The output folder will be created should it not exist prior to calling the command.
    A set of nginx configuration files will be created: one for each domain. 
    The command skips setting push/preload values for overlapping uris. 
    Only the first occurence of each source uri is included in the output. 
    This is because multiple sites may have different rules for the same uri. 
    """
    folder = args.input_folder
    result_files = []
    file_paths = list(Path(folder).rglob("*.[jJ][sS][oO][nN]"))

    number_of_overlapping_source_push_urls = 0
    number_of_unique_source_push_urls = 0

    number_of_overlapping_source_preload_urls = 0
    number_of_unique_source_preload_urls = 0


    already_seen_push_source = {}
    already_seen_preload_source = {}

    url_to_push_mapping = {} 
    url_to_preload_mapping = {}	

    for posix_file_path in file_paths:
        f = str(posix_file_path)
        try:
            with open(f, "r") as policy_file:
                policy_dict = json.load(policy_file)
        except json.JSONDecodeError as e:
            print("failed to decode json for " + f + ", err: " + str(e), file=sys.stderr)
        policy = Policy.from_dict(policy_dict)
        for ptype, policy_obj in policy_dict.items():
            if ptype == "push" or ptype == "preload":
                this_source_did_push = False
                this_source_did_preload = False
                for (source, deps) in policy_obj.items():
                    for obj in deps:
                        try:
                            if ptype == "push":
                                if source in already_seen_push_source:
                                    number_of_overlapping_source_push_urls += 1
                                    continue
                                if source not in url_to_push_mapping:
                                    url_to_push_mapping[source] = []
                                    number_of_unique_source_push_urls += 1
                                url_to_push_mapping[source].append({"url":obj["url"]})
                                this_source_did_push = True
                            elif ptype == "preload":
                                if source in already_seen_preload_source:
                                    number_of_overlapping_source_preload_urls += 1
                                    continue
                                if source not in url_to_preload_mapping:
                                    url_to_preload_mapping[source] = []
                                    number_of_unique_source_preload_urls += 1
                                url_to_preload_mapping[source].append({"url":obj["url"],"as_type":obj["type"]})
                                this_source_did_preload = True
                        except KeyError as e:
                            log.debug("have key error when trying to read policy ", error=e)
                if this_source_did_push:
                    already_seen_push_source[source] = True
                if this_source_did_preload:
                    already_seen_preload_source[source] = True

    list_of_domains = []
    domain_to_source_url_mapping = {}
    domain_to_protocol_mapping = {}

    for k in dict.keys(url_to_push_mapping):
        domain_name = urlparse(k).netloc
        if domain_name not in domain_to_protocol_mapping:
            domain_to_protocol_mapping[domain_name] = urlparse(k).scheme
        list_of_domains.append(domain_name)
        if domain_name not in domain_to_source_url_mapping:
            domain_to_source_url_mapping[domain_name] = []
        domain_to_source_url_mapping[domain_name].append(k)

    for k in dict.keys(url_to_preload_mapping):
        domain_name = urlparse(k).netloc
        if domain_name not in domain_to_protocol_mapping:
            domain_to_protocol_mapping[domain_name] = urlparse(k).scheme
        if domain_name not in list_of_domains:
            list_of_domains.append(domain_name)
        if domain_name not in domain_to_source_url_mapping:
            domain_to_source_url_mapping[domain_name] = []
        domain_to_source_url_mapping[domain_name].append(k)

    for domain, source_url_list in domain_to_source_url_mapping.items():
        config = Config()
        server_block = config.add_server(cert_path="/etc/ssl/certs/nginx-selfsigned.crt",key_path="/etc/ssl/private/nginx-selfsigned.key",server_addr="127.0.0.1",server_name=domain)
        for source in source_url_list:
            location_block = server_block.add_location_block(uri=urlparse(source).path)
            location_block.enable_proxy_server()
            if source in url_to_push_mapping:
                for item in url_to_push_mapping[source]:
                    location_block.add_push(uri=urlparse(item["url"]).path)
            if source in url_to_preload_mapping:
                for item in url_to_preload_mapping[source]:
                    location_block.add_preload(uri=item["url"], as_type=item["as_type"])
        location_block = server_block.add_location_block(uri="/",exact_match=False)
        location_block.enable_proxy_server()
        Path(args.output_folder).mkdir(parents=True, exist_ok=True)
        with open(os.path.join(args.output_folder, f'{domain}.config'), "w") as f:
            f.write(str(config))
