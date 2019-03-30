""" Defines the environment that the training of the agent occurs in """
import gym

from blaze.config import client, Config
from blaze.evaluator import Analyzer

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

    return get_observation(self.client_environment, self.train_config.push_groups, self.policy)

  def step(self, action):
    decoded_action = self.action_space.decode_action_id(action)
    action_applied = self.policy.apply_action(action)
    observation = get_observation(self.client_environment, self.train_config.push_groups, self.policy)

    reward = NOOP_ACTION_REWARD
    if action_applied:
      reward = self.analyzer.get_reward(self.policy) or NOOP_ACTION_REWARD

    print('action={action}, total_actions={total}, reward={reward}'.format(
      action=repr(decoded_action),
      total=self.policy.actions_taken,
      reward=reward,
    ))
    return observation, reward, self.policy.completed, {'action': decoded_action} 

  def render(self, mode='human'):
    return super(Environment, self).render(mode=mode)
