""" This module parses a mahimahi recorded folder so that the files can be served by nginx """

import glob
import os
import subprocess
from typing import Dict, List

from recordclass import RecordClass

from blaze.proto import http_record_pb2
from blaze.util import encoding


CACHE_CONTROL_HEADER = "cache-control"
TRANSFER_ENCODING_HEADER = "transfer-encoding"
ACCESS_CONTROL_ALLOW_ORIGIN_HEADER = "access-control-allow-origin"
REMOVE_HEADERS = [
    "cache-control",
    "connection",
    "content-length",
    "expires",
    "keep-alive",
    "last-modified",
    "date",
    "age",
    "etag",
]


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

    @property
    def file_name(self):
        """
        :return: The base name of the file path
        """
        return os.path.basename(self.file_path)

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
        res_headers = {
            h.key.decode().lower(): h.value.decode()
            for h in record.response.header
            if h.key.decode().lower() not in REMOVE_HEADERS
        }

        body = record.response.body

        # Unchunk the body if it is chunked since HTTP/2 does not support chunked encoding
        if TRANSFER_ENCODING_HEADER in res_headers and "chunked" in res_headers[TRANSFER_ENCODING_HEADER].lower():
            body = encoding.unchunk(body)
            del res_headers[TRANSFER_ENCODING_HEADER]

        out = subprocess.Popen(['/opt/blaze/blaze/mahimahi/server/iscacheable', path],
           stdout=subprocess.PIPE,
           stderr=subprocess.STDOUT)
        stdout, stderr = out.communicate()
        if stderr is not None:
            # TODO: what if we cannot read cache headers from mahimahi file, should we set 0 or 3600
            res_headers[CACHE_CONTROL_HEADER] = "0"
        else:
            if "YES" in stdout.decode('utf-8'):
                # Pushable objects must be cacheable and ignore security settings for replayed resources
                res_headers[CACHE_CONTROL_HEADER] = "3600"
            else:
                res_headers[CACHE_CONTROL_HEADER] = "0"
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


class FileStore:
    """
    A collection of Files representing recorded files by mahimahi
    """

    def __init__(self, path: str):
        """
        :param path: The path to the folder of mahimahi-recorded files
        """
        self.path = os.path.abspath(path)
        self._files = []

    @property
    def files(self) -> List[File]:
        """
        :return: A list of File objects corresponding to the files in self.path
        """
        self._files = self._files or list(map(File.read, glob.iglob(f"{self.path}/*")))
        return self._files

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
