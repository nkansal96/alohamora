import collections

import gym

from blaze.config.client import ClientEnvironment
from blaze.evaluator import Analyzer
from blaze.policy import Policy

from .action import ActionSpace
from .config import Config
from .observation import get_observation, get_observation_space

NOOP_ACTION_REWARD    = 0
INVALID_ACTION_REWARD = -100000

class Environment(gym.Env):
  def __init__(self, config: Config):
    self.config = config
    self.client_environment = ClientEnvironment()

    self.action_space = ActionSpace(config.push_groups)
    self.observation_space = get_observation_space(self.client_environment, config)

    self.policy = Policy(self.config.push_groups, self.action_space)
    self.analyzer = Analyzer(self.config.replay_dir, self.config.request_url, self.client_environment)
  
  def reset(self):
    # self.policy = Policy(self.push_groups)
    # self.analyzer = Analyzer(self.replay_dir, self.request_url, self.throttling_settings)
    return get_observation(self.client_environment, self.config, self.policy)
  
  def step(self, action):
    assert self.action_space.contains(action), "{} not found in action_space".format(action)
    action = self.policy.decode_action(action)
    print("try action {}... ".format(action), end="")

    if not self.policy.valid_action(action):
      print("invalid action (rew {})".format(INVALID_ACTION_REWARD))
      return self.policy.observation, INVALID_ACTION_REWARD, True, {"action": action}

    if not self.policy.apply_action(action):
      print("no-op action (rew {}, total_actions {})".format(NOOP_ACTION_REWARD, self.policy.actions_taken))
      return self.policy.observation, NOOP_ACTION_REWARD, self.policy.completed, {"action": action}

    reward = self.analyzer.get_reward(self.policy.push_policy) or NOOP_ACTION_REWARD
    print("valid action (rew {}, total_actions {})".format(reward, self.policy.actions_taken))
    return self.policy.observation, reward, self.policy.completed, {"action": action} 
