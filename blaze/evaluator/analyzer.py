import contextlib
import os
import sys
import time
import traceback

from blaze.config.client import ClientEnvironment
from blaze.evaluator import lighthouse
from blaze.evaluator import mahimahi

class Analyzer(object):
  def __init__(self, replay_dir: str, req_url: str, environment: ClientEnvironment):
    self.replay_dir = replay_dir
    self.req_url = req_url
    self.environment = environment
    self.min_speed_index = 1000000.0
    self.last_speed_index = None

  def get_reward(self, policy):
    try:
      with mahimahi.get_mahimahi_configuration(self.replay_dir, policy, self.environment) as mm_config:
        metrics = lighthouse.get_metrics(self.req_url, mm_config)
        speed_index = float(metrics.speed_index)
        reward = 0
        if speed_index < self.min_speed_index:
          reward = 200000.0/speed_index
        else:
          a, b = sorted([speed_index, self.last_speed_index])
          sign = -2 if speed_index > self.last_speed_index else 4
          reward = sign * (b/a)
        self.min_speed_index = min(self.min_speed_index, speed_index)
        self.last_speed_index = speed_index
        return reward
    except:
      print(traceback.format_exc())
      return None
