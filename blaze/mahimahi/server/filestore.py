""" This module parses a mahimahi recorded folder so that the files can be served by nginx """

import glob
import os
import subprocess
from typing import Dict, List, Optional

from recordclass import RecordClass

from blaze.logger import logger as log
from blaze.proto import http_record_pb2
from blaze.util import encoding


DATE_HEADER = "date"
PRAGMA_HEADER = "pragma"
EXPIRES_HEADER = "expires"
LAST_MODIFIED_HEADER = "last-modified"
CACHE_CONTROL_HEADER = "cache-control"
TRANSFER_ENCODING_HEADER = "transfer-encoding"
ACCESS_CONTROL_ALLOW_ORIGIN_HEADER = "access-control-allow-origin"
REMOVE_HEADERS = [
    "connection",
    "content-length",
    "keep-alive",
    "age",
    "etag",
    CACHE_CONTROL_HEADER,
    DATE_HEADER,
    EXPIRES_HEADER,
    LAST_MODIFIED_HEADER,
    PRAGMA_HEADER,
    TRANSFER_ENCODING_HEADER,
]


def check_cacheability(headers: Dict[str, str]) -> bool:
    """
    Checks whether a resource with the given headers is cacheable or not
    """
    cache_control = headers.get(CACHE_CONTROL_HEADER, "")
    if "no-cache" in cache_control or "no-store" in cache_control:
        return False

    if "max-age=" in cache_control:
        try:
            max_age = int(cache_control.split("max-age=")[1].split(",")[0])
            if max_age > 0:
                return True
        except ValueError:
            pass

    pragma = headers.get(PRAGMA_HEADER, "")
    if "no-cache" in pragma:
        return False

    expires = headers.get(EXPIRES_HEADER, False)
    last_modified = headers.get(LAST_MODIFIED_HEADER, False)
    return expires != "0" if expires else last_modified


def get_cache_times(file_dir: str) -> Dict[str, int]:
    """
    :return: a dictionary mapping each file name to its freshness using `findcacheable`
    """

    def demote():
        if os.path.isfile("/opt/entrypoint.sh"):
            os.setgid(27)
            os.setuid(103)

    path = os.environ.get("FINDCACHEABLE_BIN", os.path.join(os.path.dirname(__file__), "findcacheable"))
    proc = subprocess.run(
        f"{path} '{file_dir}/' | awk -F'/' '{{print $NF'}} | grep freshness",
        shell=True,
        preexec_fn=demote,
        stdout=subprocess.PIPE,
    )
    if proc.returncode != 0:
        log.with_namespace("get_cache_times").warn("failed to run findcacheable", code=proc.returncode)
    d = {}
    for line in proc.stdout.decode("utf-8").strip().split("\n"):
        try:
            fname, time = line.strip().split(" freshness=")
            d[fname] = int(time)
        except ValueError:
            continue
    return d


class File(RecordClass):
    """
    A File is a logical entry in the filestore, representing the metadata and body of a particular file in
    a mahimahi recorded directory
    """

    # The file path to the (mahimahi-recorded) file this object represents
    file_path: str

    # Request parameters
    method: str
    uri: str
    host: str

    # Response parameters
    headers: dict
    status: int
    body: bytes

    # Convenience metadata
    cache_time: int = 0

    @property
    def file_name(self):
        """
        :return: The base name of the file path
        """
        return os.path.basename(self.file_path)

    @property
    def url(self):
        """
        :return: The full URL of this resources
        """
        return f"https://{self.host}{self.uri}"

    @staticmethod
    def read(path: str) -> "File":
        """
        Reads and process a mahimahi protobuf
        :param path: The file to process
        :return: a File object
        """
        # pylint doesn't work great with generate protobuf code
        # pylint: disable=no-member
        with open(path, "rb") as f:
            record = http_record_pb2.RequestResponse()
            record.ParseFromString(f.read())

        # Decode headers from a list of pairs to a dictionary, decoding bytes to str and converting to lowercase
        # to make easier parsing. Also remove headers that we don't want to send back in a replayed response
        req_headers = {h.key.decode().lower(): h.value.decode() for h in record.request.header}
        res_headers = {h.key.decode().lower(): h.value.decode() for h in record.response.header}

        # Unchunk the body if it is chunked since HTTP/2 does not support chunked encoding
        body = record.response.body
        if TRANSFER_ENCODING_HEADER in res_headers and "chunked" in res_headers[TRANSFER_ENCODING_HEADER].lower():
            body = encoding.unchunk(body)

        # Remove the unnecessary headers after checking transer encoding
        res_headers = {k: v for (k, v) in res_headers.items() if k not in REMOVE_HEADERS}
        if ACCESS_CONTROL_ALLOW_ORIGIN_HEADER not in res_headers:
            res_headers[ACCESS_CONTROL_ALLOW_ORIGIN_HEADER] = "*"

        method, uri, *_ = record.request.first_line.decode().split(" ")
        _, status, *_ = record.response.first_line.decode().split(" ")
        host = req_headers["host"]

        # it doesn't work when specifying the 'typename' parameter, but pylint complains
        # pylint: disable=no-value-for-parameter
        return File(
            file_path=path, method=method, uri=uri, host=host, headers=res_headers, status=int(status), body=body
        )

    def set_cache_time(self, cache_time: int):
        """ Sets the amount of time this object is cacheable for and adds the Cache-Control header """
        self.cache_time = cache_time
        self.headers[CACHE_CONTROL_HEADER] = str(cache_time)


class FileStore:
    """
    A collection of Files representing recorded files by mahimahi
    """

    def __init__(self, path: str, cache_time: Optional[int] = None):
        """
        :param path: The path to the folder of mahimahi-recorded files
        """
        self.path = os.path.abspath(path)
        self.cache_time = cache_time
        self._cache_times = {}
        self._files = []

    @property
    def files(self) -> List[File]:
        """
        :return: A list of File objects corresponding to the files in self.path
        """
        if not self._files:
            self._cache_times = get_cache_times(self.path)
            self._files = self._files or list(map(File.read, glob.iglob(f"{self.path}/*")))
            for f in self._files:
                cache_time = self._cache_times.get(f.file_name, 0)
                if self.cache_time is None and cache_time > 0:
                    f.set_cache_time(cache_time)
                elif self.cache_time is not None and cache_time > self.cache_time:
                    f.set_cache_time(cache_time)
                else:
                    log.with_namespace("filestore").debug(
                        "skipping setting cache", url=f.url, actual_cache_time=cache_time, cache_time=self.cache_time
                    )

        return self._files

    @property
    def cacheable_files(self) -> List[File]:
        """
        :return: A list of File objects that are cacheable
        """
        return [f for f in self.files if f.cache_time > 0]

    @property
    def files_by_host(self) -> Dict[str, List[File]]:
        """
        :return: The same files as self.files, except grouped by host (domain)
        """
        d = {}
        for file in self.files:
            if file.host not in d:
                d[file.host] = []
            d[file.host].append(file)
        return d

    @property
    def hosts(self) -> List[str]:
        """
        :return: A list of all hosts in the file store
        """
        return list(set(file.host for file in self.files))
