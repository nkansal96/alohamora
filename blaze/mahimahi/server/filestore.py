import glob
import os
from recordclass import RecordClass
from typing import Dict, List

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
    file_path: str

    method: str
    uri: str
    host: str

    headers: dict
    body: bytes

    @property
    def file_name(self):
        return os.path.basename(self.file_path)

    @staticmethod
    def read(path: str) -> "File":
        """
        Reads and process a mahimahi protobuf
        :param path: The file to process
        :return: a File object
        """
        with open(path, "rb") as f:
            record = http_record_pb2.RequestResponse()
            record.ParseFromString(f.read())

        body = record.response.body
        req_headers = {h.key.decode().lower(): h.value.decode() for h in record.request.header}
        res_headers = {
            h.key.decode().lower(): h.value.decode()
            for h in record.response.header
            if h.key.decode().lower() not in REMOVE_HEADERS
        }

        if TRANSFER_ENCODING_HEADER in res_headers and "chunked" in res_headers[TRANSFER_ENCODING_HEADER].lower():
            body = encoding.unchunk(body)
            del res_headers[TRANSFER_ENCODING_HEADER]

        res_headers[CACHE_CONTROL_HEADER] = "3600"
        if ACCESS_CONTROL_ALLOW_ORIGIN_HEADER not in res_headers:
            res_headers[ACCESS_CONTROL_ALLOW_ORIGIN_HEADER] = "*"

        method, uri, *_ = record.request.first_line.decode().split(" ")
        host = req_headers["host"]
        return File(file_path=path, method=method, uri=uri, host=host, headers=res_headers, body=body)


class FileStore:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self._files = []

    @property
    def files(self):
        self._files = self._files or list(map(File.read, glob.iglob(f"{self.path}/*")))
        return self._files

    @property
    def files_by_host(self) -> Dict[str, List[File]]:
        d = {}
        for file in self.files:
            if file.host not in d:
                d[file.host] = []
            d[file.host].append(file)
        return d

    @property
    def hosts(self) -> List[str]:
        return list(set(file.host for file in self.files))


f = FileStore("/Users/nkansal/Documents/School/CS/239_Web/push-policy/testing/site_1")
# fs = f.files
for fs in f.files_by_host.values():
    for fi in fs:
        print(fi.method, fi.uri, fi.headers)

print(f.hosts)
