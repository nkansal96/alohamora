""" Defines the environment that the training of the agent occurs in """
from typing import Optional, Union

import gym

from blaze.action import ActionIDType, ActionSpace, Policy
from blaze.config import client, Config
from blaze.config.client import ClientEnvironment
from blaze.evaluator import Analyzer
from blaze.logger import logger as log

from .observation import get_observation, get_observation_space

NOOP_ACTION_REWARD = 0


class Environment(gym.Env):
    """
    Environment virtualizes a randomly chosen network and browser environment and
    facilitates the training for a given web page. This includes action selection, policy
    generation, and evaluation of the policy/action in the simulated environment.
    """

    def __init__(self, config: Union[Config, dict]):
        # make sure config is an instance of Config or a dict
        assert isinstance(config, (Config, dict))
        config = config if isinstance(config, Config) else Config(**config)

        self.config = config
        self.env_config = config.env_config

        log.info(
            "initialized trainable push groups", groups=[group.name for group in self.env_config.trainable_push_groups]
        )

        self.observation_space = get_observation_space()
        self.analyzer = Analyzer(self.config)

        self.client_environment: Optional[ClientEnvironment] = None
        self.action_space: Optional[ActionSpace] = None
        self.policy: Optional[Policy] = None
        self.initialize_environment(client.get_random_fast_lte_client_environment())

    def reset(self):
        self.initialize_environment(client.get_random_fast_lte_client_environment())
        return self.observation

    def initialize_environment(self, client_environment):
        """ Initialize the environment """
        log.info(
            "initialized environment",
            network_type=client.NetworkType(client_environment.network_type),
            network_speed=client.NetworkSpeed(client_environment.network_speed),
            device_speed=client.DeviceSpeed(client_environment.device_speed),
            bandwidth=client_environment.bandwidth,
            latency=client_environment.latency,
            cpu_slowdown=client_environment.cpu_slowdown,
        )
        self.client_environment = client_environment
        self.analyzer.reset(self.client_environment)

        self.action_space = ActionSpace(self.env_config.push_groups)
        self.policy = Policy(self.action_space)

        # choose a random non-trainable push group to simulate as if it's already pushed
        # candidate_push_groups = [
        #     group for group in self.env_config.push_groups if len(group.resources) > 2 and not group.trainable
        # ]
        # if candidate_push_groups:
        #     default_group = random.choice(candidate_push_groups)
        #     for push in default_group.resources[1:]:
        #         self.policy.add_default_push_action(default_group.resources[0], push)
        #     log.info("chose group to auto push", group=default_group.name, rules_added=len(default_group.resources))

    def step(self, action: ActionIDType):
        decoded_action = self.action_space.decode_action(action)
        action_applied = self.policy.apply_action(decoded_action)
        log.info("trying action", action=repr(decoded_action), steps_taken=self.policy.steps_taken)

        reward = NOOP_ACTION_REWARD
        if action_applied:
            self.action_space.use_action(decoded_action)
            reward = self.analyzer.get_reward(self.policy) or NOOP_ACTION_REWARD
        log.info("got reward", action=repr(decoded_action), reward=reward)

        info = {"action": decoded_action, "policy": self.policy.as_dict}
        return self.observation, reward, decoded_action.is_noop, info

    def render(self, mode="human"):
        return super(Environment, self).render(mode=mode)

    @property
    def observation(self):
        """ Returns an observation for the current state of the environment """
        return get_observation(self.client_environment, self.env_config.push_groups, self.policy)
