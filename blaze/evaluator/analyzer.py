"""
This module defines the analyzer which tests a push policy by loading the page
under the specified circumstances and returns a metric indicating the policy
quality
"""

from typing import Optional

from blaze.action import Policy
from blaze.config import client, Config
from blaze.evaluator import lighthouse
from blaze.logger import logger
from blaze.mahimahi import mahimahi

MIN_SPEED_INDEX = 1000000.0
BEST_REWARD_COEFF = 200000.0
REGRESSION_REWARD_COEFF = -2.0
PROGRESSION_REWARD_COEFF = 4.0

class Analyzer():
  """
  Analyzer loads a page with some push policy in a configured client environment
  and evaluates how good the policy is. The reward is based on the speed index
  metric and considers whether the push policy produced the best speed index so far,
  a better speed index than the previous policy, or a worse speed index than the
  previous policy
  """
  def __init__(self, config: Config, client_environment: Optional[client.ClientEnvironment] = None):
    self.config = config
    self.client_environment = client_environment
    self.min_speed_index = MIN_SPEED_INDEX
    self.last_speed_index = None

  def reset(self, client_environment: Optional[client.ClientEnvironment] = None):
    """ Resets the analyzer's state and optionally changes the client environment """
    self.client_environment = client_environment or self.client_environment
    self.min_speed_index = MIN_SPEED_INDEX
    self.last_speed_index = None

  def get_reward(self, policy: Policy):
    """
    Evaluates the given push policy by instantiating a Mahimahi environment simulating
    the client environment and the page load. It calculates the reward based on the
    resulting speed index returned from Lighthouse
    """
    log = logger.with_namespace('analyzer')
    log.debug('analyzing web page...')
    mm_config = mahimahi.MahiMahiConfig(self.config, policy, self.client_environment)
    metrics = lighthouse.get_metrics(self.config, mm_config)
    speed_index = float(metrics.speed_index)
    reward = 0
    if speed_index < self.min_speed_index:
      log.debug('received best speed index', speed_index=speed_index)
      reward = BEST_REWARD_COEFF/speed_index
    else:
      a, b = sorted([speed_index, self.last_speed_index])
      sign = REGRESSION_REWARD_COEFF if speed_index > self.last_speed_index else PROGRESSION_REWARD_COEFF
      log.debug('received {} speed index'.format('better' if sign > 0 else 'worse'), speed_index=speed_index)
      reward = sign * (b/a)
    self.min_speed_index = min(self.min_speed_index, speed_index)
    self.last_speed_index = speed_index
    return reward
