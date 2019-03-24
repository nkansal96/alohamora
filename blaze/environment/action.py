from typing import List

import gym
import numpy as np

from .config import PushGroup, Resource

class Action(object):
  def __init__(self, push_groups: List[PushGroup], g: int, s: int, p: int):
    self.push_groups = push_groups
    self.g = g
    self.s = s
    self.p = p
  
  @property
  def source(self):
    return self.push_groups[self.g][self.s]
  
  @property
  def push(self):
    return self.push_groups[self.g][self.p]
  
  @property
  def is_noop(self):
    return self.p == 0

class ActionSpace(gym.spaces.Space):
  def __init__(self, push_groups: List[PushGroup]):
    super(ActionSpace, self).__init__((), np.int64)
    self.rand = np.random.RandomState()
    self.push_groups = push_groups
    # self.push_resources = sorted([
    #   res for group in push_groups for res in group
    # ], key=lambda r: r.order)

  
  def seed(self, seed):
    self.rand.seed(seed)
  
  def sample(self):
    # TODO: implement this
    return 0
  
  def contains(self):
    # TODO: implement this
    return True
  
  def decode_action(self, action_id) -> Action:
    return self.actions[action_id]

  def use_action(self, action_id):
    del self.actions[action_id]
  
  def __repr__(self):
    return "ActionSpace(List[PushGroup])"
