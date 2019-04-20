""" Defines methods and classes for representing and instantiating saved models """
from typing import NamedTuple

import gym
from ray.rllib.agents import Agent

from blaze.action import ActionSpace, Policy
from blaze.config.environment import EnvironmentConfig
from blaze.config.client import ClientEnvironment
from blaze.environment.observation import get_observation

class ModelInstance():
  """
  A loaded instance of a saved model. This class allows for the generation of a push policy given
  an environment and client configuration
  """
  def __init__(self, agent: Agent, env_config: EnvironmentConfig, client_environment: ClientEnvironment):
    self.agent = agent
    self.client_environment = client_environment
    self.env_config = env_config
    self.policy = None

  @property
  def push_policy(self) -> Policy:
    """
    Generates (and caches) the push policy from the loaded model based on the given environment
    and client configuration
    """
    # check if the policy has been cached
    if self.policy is not None:
      return self.policy
    # create ActionSpace and Policy objects to record the actions taken by the agent
    trainable_push_groups = [group for group in self.env_config.push_groups if group.trainable]
    action_space = ActionSpace(trainable_push_groups)
    self.policy = Policy(action_space)
    # create the initial observation from the environment that gets passed to the agent
    observation = get_observation(self.client_environment, self.env_config.push_groups, self.policy)
    # keep querying the agent until the policy is complete
    while not self.policy.completed:
      # query the agent for an action
      action = self.agent.compute_action(observation)
      # apply the action to the policy
      self.policy.apply_action(action)
      # update the observation based on the action
      observation = get_observation(self.client_environment, self.env_config.push_groups, self.policy)
    return self.policy

class SavedModel(NamedTuple):
  """
  A saved model, combining the agent type (APEX, PPO, etc.), the environment used for
  training (typically blaze.environment.Environment), and the directory containing the
  checkpoint file from training the model
  """
  cls: Agent
  env: gym.Env
  location: str

  def instantiate(self, env_config: EnvironmentConfig, client_environment: ClientEnvironment) -> ModelInstance:
    """ Instantiates the saved model and returns a ModelInstance for the given environment """
    agent = self.cls(env=self.env, config={"env_config": env_config})
    agent.restore(self.location)
    model_instance = ModelInstance(agent, env_config, client_environment)
    return model_instance
