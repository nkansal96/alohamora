""" Defines methods and classes for representing and instantiating saved models """
from typing import NamedTuple, Optional, Type

import gym
from ray.rllib.agents import Agent

from blaze.action import Action, ActionSpace, Policy
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.config.client import ClientEnvironment
from blaze.environment.observation import get_observation


class ModelInstance:
    """
    A loaded instance of a saved model. This class allows for the generation of a push policy given
    an environment and client configuration
    """

    def __init__(self, agent: Agent, env_config: EnvironmentConfig, client_environment: ClientEnvironment):
        self.agent = agent
        self.client_environment = client_environment
        self.env_config = env_config
        self._policy = None

    @property
    def policy(self) -> Policy:
        """
        Generates (and caches) the push policy from the loaded model based on the given environment
        and client configuration
        """
        # check if the policy has been cached
        if self._policy is not None:
            return self._policy
        # create ActionSpace and Policy objects to record the actions taken by the agent
        action_space = ActionSpace(self.env_config.trainable_push_groups)
        self._policy = Policy(action_space)
        # create the initial observation from the environment that gets passed to the agent
        observation = get_observation(self.client_environment, self.env_config.push_groups, self._policy)
        last_action: Optional[Action] = None
        # keep querying the agent until the policy is complete
        while not last_action or not last_action.is_noop:
            # query the agent for an action
            action = self.agent.compute_action(observation)
            # deflate the action
            action = tuple(x[0] for x in action)
            last_action = action_space.decode_action(action)
            # apply the action to the policy
            self.policy.apply_action(last_action)
            # update the observation based on the action
            observation = get_observation(self.client_environment, self.env_config.push_groups, self.policy)
        return self.policy


class SavedModel(NamedTuple):
    """
    A saved model, combining the agent type (APEX, PPO, etc.), the environment used for
    training (typically blaze.environment.Environment), and the directory containing the
    checkpoint file from training the model
    """

    cls: Type[Agent]
    env: Type[gym.Env]
    location: str

    def instantiate(self, env_config: EnvironmentConfig, client_environment: ClientEnvironment) -> ModelInstance:
        """ Instantiates the saved model and returns a ModelInstance for the given environment """
        agent = self.cls(env=self.env, config={"env_config": get_config(env_config)})
        agent.restore(self.location)
        model_instance = ModelInstance(agent, env_config, client_environment)
        return model_instance
