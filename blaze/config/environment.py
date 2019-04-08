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
  FONT = 5
  OTHER = 6

class Resource(NamedTuple):
  """ Resource defines a particular resource in a page """
  url: str
  size: int
  order: int
  group_id: int
  source_id: int
  type: ResourceType

  def __eq__(self, other):
    return self.url == other.url

  def __ne__(self, other):
    return not self == other

  def __hash__(self):
    return hash(self.url)

class PushGroup(NamedTuple):
  """ PushGroup collects a group of resources for the same domain """
  group_name: str
  resources: List[Resource]

class EnvironmentConfig(NamedTuple):
  """ EnvironmentConfig is the main configuration used in setting up the training environment """
  replay_dir: str
  request_url: str
  push_groups: List[PushGroup]
