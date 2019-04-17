""" Defines the environment that the training of the agent occurs in """
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

    log.info(
      'initializing environment',
      network_type=client_environment.network_type,
      network_speed=client_environment.network_speed,
      device_speed=client_environment.device_speed,
    )

    self.config = config
    self.train_config = config.train_config
    self.client_environment = client_environment

    self.action_space = ActionSpace(self.train_config.push_groups)
    self.observation_space = get_observation_space()

    self.policy = Policy(self.action_space)
    self.analyzer = Analyzer(self.config, self.client_environment)

  def reset(self):
    self.action_space = ActionSpace(self.train_config.push_groups)
    self.policy = Policy(self.action_space)

    self.client_environment = client.get_random_client_environment()
    self.analyzer.reset(self.client_environment)

    log.info(
      'initializing environment',
      network_type=self.client_environment.network_type,
      network_speed=self.client_environment.network_speed,
      device_speed=self.client_environment.device_speed,
    )

    return self.observation

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
    return get_observation(self.client_environment, self.train_config.push_groups, self.policy)
