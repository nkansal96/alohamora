""" Defines methods and classes for representing and instantiating saved models """
from typing import NamedTuple, Optional, Type

import gym
from ray.rllib.agents import Agent
from ray.rllib.evaluation.episode import _flatten_action
from ray.rllib.policy.sample_batch import DEFAULT_POLICY_ID

from blaze.action import Policy
from blaze.config.config import Config
from blaze.environment.environment import Environment


class ModelInstance:
    """
    A loaded instance of a saved model. This class allows for the generation of a push policy given
    an environment and client configuration
    """

    def __init__(self, agent: Agent, config: Config):
        self.agent = agent
        self.config = config
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
        # initialize LSTM state if applicable
        policy_map = self.agent.workers.local_worker().policy_map if hasattr(self.agent, "workers") else {}
        state = policy_map.get(DEFAULT_POLICY_ID, [])
        use_lstm = len(state) > 0

        while not completed:
            # query the agent for an action
            if use_lstm:
                action, state, _ = self.agent.compute_action(obs, state=state, prev_action=action, prev_reward=reward)
            else:
                action = self.agent.compute_action(obs, prev_action=action, prev_reward=reward)
            action = _flatten_action(action)
            # deflate and apply the action
            obs, reward, completed, _ = env.step(action)
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

    def instantiate(self, config: Config) -> ModelInstance:
        """ Instantiates the saved model and returns a ModelInstance for the given environment """
        agent = self.cls(env=self.env, config={**self.common_config, "env_config": config})
        agent.restore(self.location)
        return ModelInstance(agent, config)
