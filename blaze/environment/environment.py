""" Defines the environment that the training of the agent occurs in """
import random

import gym

from blaze.config import client, Config
from blaze.evaluator import Analyzer
from blaze.logger import logger as log

from blaze.action import ActionSpace, Policy
from .observation import get_observation, get_observation_space

NOOP_ACTION_REWARD = 0

class Environment(gym.Env):
  """
  Environment virtualizes a randomly chosen network and browser environment and
  faciliates the training for a given webpage. This includes action selection, policy
  generation, and evaluation of the policy/action in the simulated environment.
  """
  def __init__(self, config: Config, client_environment=client.get_random_client_environment()):
    # make sure config is an instance of Config or a dict
    assert isinstance(config, (Config, dict))
    config = config if isinstance(config, Config) else Config(**config)

    self.config = config
    self.env_config = config.env_config
    self.trainable_push_groups = [group for group in self.env_config.push_groups if group.trainable]
    log.info(
      'initialized trainable push groups',
      groups=[group.group_name for group in self.trainable_push_groups],
    )
    
    self.observation_space = get_observation_space()
    self.analyzer = Analyzer(self.config)
    self.initialize_environment(client_environment)

  def reset(self):
    self.initialize_environment()
    return self.observation

  def initialize_environment(self, client_environment=client.get_random_client_environment()):
    """ Initialize the environment """
    log.info(
      'initialized environment',
      network_type=client_environment.network_type,
      network_speed=client_environment.network_speed,
      device_speed=client_environment.device_speed,
    )
    self.client_environment = client_environment
    self.analyzer.reset(self.client_environment)

    self.action_space = ActionSpace(self.trainable_push_groups)
    self.policy = Policy(self.action_space)

    # choose a random non-trainable push group to simulate as if it's already pushed
    candidate_push_groups = [group for group in self.env_config.push_groups
                             if len(group.resources) > 2 and not group.trainable]
    if candidate_push_groups:
      default_group = random.choice(candidate_push_groups)
      for push in default_group.resources[1:]:
        self.policy.add_default_action(default_group.resources[0], push)
      log.info(
        'chose group to auto push',
        group=default_group.group_name,
        rules_added=len(default_group.resources) - 1
      )

  def step(self, action):
    decoded_action = self.action_space.decode_action_id(action)
    action_applied = self.policy.apply_action(action)

    reward = NOOP_ACTION_REWARD
    if action_applied:
      reward = self.analyzer.get_reward(self.policy) or NOOP_ACTION_REWARD

    log.info(
      'took action',
      action=repr(decoded_action),
      total_actions=self.policy.actions_taken,
      reward=reward,
    )

    return self.observation, reward, self.policy.completed, {'action': decoded_action}

  def render(self, mode='human'):
    return super(Environment, self).render(mode=mode)

  @property
  def observation(self):
    """ Returns an observation for the current state of the environment """
    return get_observation(self.client_environment, self.env_config.push_groups, self.policy)
