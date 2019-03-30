""" Describes types used to configure the training environment """

from typing import List, NamedTuple
import enum

class ResourceType(enum.IntEnum):
  """ ResourceType defines the type of a particular resource """
  NONE = 0
  HTML = 1
  SCRIPT = 2
  CSS = 3
  IMAGE = 4
  OTHER = 5

class Resource(NamedTuple):
  """ Resource defines a particular resource in a page """
  url: str
  size: int
  order: int
  group_id: int
  source_id: int
  type: ResourceType

class PushGroup(NamedTuple):
  """ PushGroup collects a group of resources for the same domain """
  group_name: str
  resources: List[Resource]

class TrainConfig(NamedTuple):
  """ TrainConfig is the main configuration used in setting up the training environment """
  replay_dir: str
  request_url: str
  push_groups: List[PushGroup]
