""" Defines methods and classes for representing and instantiating saved models """
from typing import NamedTuple, Optional, Type

import gym
from ray.rllib.agents import Agent

from blaze.action import Policy
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.config.client import ClientEnvironment
from blaze.environment.environment import Environment


class ModelInstance:
    """
    A loaded instance of a saved model. This class allows for the generation of a push policy given
    an environment and client configuration
    """

    def __init__(self, agent: Agent, env_config: EnvironmentConfig, client_env: ClientEnvironment):
        self.agent = agent
        self.client_env = client_env
        self.env_config = env_config
        self.config = get_config(self.env_config, self.client_env)
        self._policy: Optional[Policy] = None

    @property
    def policy(self) -> Policy:
        """
        Generates (and caches) the push policy from the loaded model based on the given environment
        and client configuration
        """
        # check if the policy has been cached
        if self._policy is not None:
            return self._policy
        # create the environment that the agent acts in
        env = Environment(self.config)
        # keep querying the agent until the policy is complete
        obs, action, reward, completed = env.observation, None, None, False
        while not completed:
            # query the agent for an action
            action = self.agent.compute_action(obs, prev_action=action, prev_reward=reward)
            # deflate and apply the action
            obs, reward, completed, _ = env.step(tuple(x[0] for x in action))
        self._policy = env.policy
        return self._policy


class SavedModel(NamedTuple):
    """
    A saved model, combining the agent type (APEX, PPO, etc.), the environment used for
    training (typically blaze.environment.Environment), and the directory containing the
    checkpoint file from training the model
    """

    cls: Type[Agent]
    env: Type[gym.Env]
    location: str
    common_config: dict

    def instantiate(self, env_config: EnvironmentConfig, client_env: ClientEnvironment) -> ModelInstance:
        """ Instantiates the saved model and returns a ModelInstance for the given environment """
        agent = self.cls(env=self.env, config={**self.common_config, "env_config": get_config(env_config, client_env)})
        agent.restore(self.location)
        return ModelInstance(agent, env_config, client_env)
