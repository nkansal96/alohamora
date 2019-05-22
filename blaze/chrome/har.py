"""
This module defines HAR files and implements some basic methods to create and
manipulate them
"""

import json
from types import SimpleNamespace
from typing import NewType, Union

Har = NewType("Har", SimpleNamespace)


def har_from_json(har_json: Union[str, bytes]) -> Har:
    """ Returns a Har instance from JSON data """
    return json.loads(har_json, object_hook=lambda d: SimpleNamespace(**d))
