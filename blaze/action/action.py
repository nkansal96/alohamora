"""
This module contains the main class representing an action that an agent can
take when exploring push policies
"""

from typing import Optional

from blaze.config.environment import Resource

class Action():
  """
  Action describes a single, valid action that the agent can take. It consists of
  a pair of resources (source, push) which describe the resource that should be pushed
  upon a request for a given resource
  """
  def __init__(self, action_id: int = 0, source: Optional[Resource] = None, push: Optional[Resource] = None):
    self.action_id = action_id
    self.source = source
    self.push = push

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
