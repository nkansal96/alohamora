"""
This module defines classes and methods related to tracking push policies
throughout a training episode and converting between the action space
representation and the actual URL representation
"""

import collections
from typing import Optional

from blaze.config.train import Resource
from .action_space import ActionSpace

class Policy():
  """
  Policy defines the current push policy, marks actions as used as they are used,
  and provides functions to help convert the policy to a URL-based format
  """
  def __init__(self, action_space: ActionSpace):
    self.action_space = action_space
    self.total_actions = len(action_space)
    self.actions_taken = 0
    self.push_to_source = {}
    self.source_to_push = collections.defaultdict(list)
    self.source_to_push_urls = collections.defaultdict(list)

  def __iter__(self):
    return iter(self.source_to_push.items())

  def __len__(self):
    return self.actions_taken

  @property
  def completed(self):
    """ Returns true if all actions have been taken """
    return self.actions_taken >= self.total_actions

  def apply_action(self, action_id: int):
    """ Given an encoded action, applies the action towards the push policy """
    action = self.action_space.decode_action_id(action_id)
    if not action.is_noop:
      self.push_to_source[action.push] = action.source
      self.source_to_push[action.source].append(action.push)
      self.source_to_push_urls[action.source.url].append(action.push.url)
      self.action_space.use_action(action)
    self.actions_taken += 1
    return not action.is_noop

  def resource_pushed_from(self, res: Resource) -> Optional[Resource]:
    """
    Returns the order (number) of the resource that the given resource was
    pushed from. Returns 0 if the resource was not pushed
    """
    if res not in self.push_to_source:
      return None
    return self.push_to_source[res]
