"""
This module defines HAR files and implements some basic methods to create and
manipulate them
"""

import json
from typing import Dict, List, NamedTuple, Union


class Timing(NamedTuple):
    """ Timing Represents timing information collected about a particular resource """

    # time in milliseconds since UNIX epoch when the request was initiated
    initiated_at: int
    # time in milliseconds since UNIX epoch when the request was finished
    finished_at: int
    # duration in milliseconds that the browser spent executing this resource (only meaningful if script)
    execution_ms: int
    # delay relative to parent resource's execution start time until this resource started downloading
    fetch_delay_ms: int
    # delay between the time the request was sent and the time the first byte was received
    time_to_first_byte_ms: int
    # the URL of the resource that initiated a request for this URL
    initiator: str


class Request(NamedTuple):
    """ The request made by the HAR capturer """

    url: str
    method: str


class Response(NamedTuple):
    """ The response captured by the HAR capturer """

    status: int
    body_size: int
    headers_size: int
    mime_type: str = ""


class HarEntry(NamedTuple):
    """ A resource recorded by the HAR capturer """

    started_date_time: str
    request: Request
    response: Response


class HarLog(NamedTuple):
    """ The HAR "log", whatever that means """

    entries: List[HarEntry]


class Har(NamedTuple):
    """ The captured HAR information, in addition to timing information for each resource """

    log: HarLog
    # maps resource URL to timing information about it
    timings: Dict[str, Timing]
    # the amount of time until the `onload` event
    page_load_time_ms: float = 0.0


JSON_CLASS_MAP = {frozenset(c._fields): c for c in [Request, Response, HarEntry, HarLog, Har, Timing]}


def har_from_json(har_json: Union[str, bytes]) -> Har:
    """
    Returns a Har instance from JSON data. Note that this HAR format is not the same as the one
    specified by the Chromium specification. See the Har data structure to see that kind of
    information is recorded.
    """

    def class_mapper(obj):
        # if not obj:
        #     return obj
        # if frozenset(obj.keys()) in JSON_CLASS_MAP:
        #     return JSON_CLASS_MAP[frozenset(obj.keys())](**obj)
        # raise obj
        for keys, cls in JSON_CLASS_MAP.items():
            if keys.issuperset(obj.keys()):
                return cls(**obj)
        return obj

    return json.loads(har_json, object_hook=class_mapper)
