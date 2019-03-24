from typing import List
import enum

class ResourceType(enum.IntEnum):
  HTML   = 1
  SCRIPT = 2
  CSS    = 3
  IMAGE  = 4
  OTHER  = 5

class Resource(object):
  def __init__(self, url: str, order: int, type: ResourceType):
    self.url = url
    self.order = order
    self.type = type

class PushGroup(object):
  def __init__(self, group_name: str, urls: List[Resource]):
    self.group_name = group_name
    self.urls = urls

class Config(object):
  def __init__(self, replay_dir: str, request_url: str, push_groups: List[PushGroup] = []):
    self.replay_dir = replay_dir
    self.request_url = request_url
    self.push_groups = push_groups
