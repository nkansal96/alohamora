"""
This module contains the main class representing an action that an agent can
take when exploring push policies
"""

from typing import List

from blaze.config.train import PushGroup, Resource

class Action():
  """
  Action describes a single, valid action that the agent can take. It consists of
  a pair of resources (source, push) which describe the resource that should be pushed
  upon a request for a given resource
  """
  def __init__(self, action_id: int = 0, g: int = 0, s: int = 0, p: int = 0, push_groups: List[PushGroup] = None):
    self.action_id = action_id
    self.g = g
    self.s = s
    self.p = p
    self.push_groups = push_groups or []

  @property
  def source(self) -> Resource:
    """ Return the source resource for this action """
    return self.push_groups[self.g].resources[self.s]

  @property
  def push(self) -> Resource:
    """ Return the push resource for this action """
    return self.push_groups[self.g].resources[self.p]

  @property
  def is_noop(self):
    """ Returns true if this action is a no-op """
    return self.action_id == 0

  def __repr__(self):
    if self.is_noop:
      return 'Action(noop)'
    return 'Action(source={}, push={})'.format(self.source.url, self.push.url)

  def __eq__(self, action):
    return self.action_id == action.action_id
