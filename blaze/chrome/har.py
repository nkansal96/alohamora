import json
from types import SimpleNamespace
from typing import Union

def convert_json_to_har(har_json: Union[str, bytes]):
  """ Convert json data to python objects """
  return json.loads(har_json, object_hook=lambda d: SimpleNamespace(**d))
