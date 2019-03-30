from typing import Optional

from blaze.config import client, Config
from blaze.evaluator import lighthouse
from blaze.mahimahi import mahimahi

MIN_SPEED_INDEX = 1000000.0
BEST_REWARD_COEFF = 200000.0
REGRESSION_REWARD_COEFF = -2.0
PROGRESSION_REWARD_COEFF = 4.0

class Analyzer():
  def __init__(self, config: Config, client_environment: client.ClientEnvironment):
    self.config = config
    self.client_environment = client_environment
    self.min_speed_index = MIN_SPEED_INDEX
    self.last_speed_index = None

  def reset(self, client_environment: Optional[client.ClientEnvironment] = None):
    self.client_environment = client_environment or self.client_environment
    self.min_speed_index = MIN_SPEED_INDEX
    self.last_speed_index = None

  def get_reward(self, policy):
    mm_config = mahimahi.MahiMahiConfig(self.config, policy, self.client_environment)
    metrics = lighthouse.get_metrics(self.config, mm_config)
    speed_index = float(metrics.speed_index)
    reward = 0
    if speed_index < self.min_speed_index:
      reward = BEST_REWARD_COEFF/speed_index
    else:
      a, b = sorted([speed_index, self.last_speed_index])
      sign = REGRESSION_REWARD_COEFF if speed_index > self.last_speed_index else PROGRESSION_REWARD_COEFF
      reward = sign * (b/a)
    self.min_speed_index = min(self.min_speed_index, speed_index)
    self.last_speed_index = speed_index
    return reward
