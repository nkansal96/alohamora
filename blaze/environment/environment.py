""" Defines the environment that the training of the agent occurs in """

import math
from typing import Optional, Set, Union

import gym
import numpy as np

from blaze.action import ActionIDType, ActionSpace, Policy
from blaze.config import client, Config
from blaze.config.client import ClientEnvironment
from blaze.evaluator import Analyzer
from blaze.logger import logger as log

from .observation import get_observation, get_observation_space

PROPORTION_DEPLOYED = 1.0
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
        self.np_random = np.random.RandomState()

        log.info(
            "initialized trainable push groups", groups=[group.name for group in self.env_config.trainable_push_groups]
        )

        self.observation_space = get_observation_space()
        self.cached_urls = config.cached_urls or set()
        self.analyzer = Analyzer(self.config, config.reward_func or 0, config.use_aft or False)

        self.client_environment: Optional[ClientEnvironment] = None
        self.action_space: Optional[ActionSpace] = None
        self.policy: Optional[Policy] = None
        self.initialize_environment(
            self.config.client_env or client.get_random_fast_lte_client_environment(), self.config.cached_urls
        )

    def seed(self, seed=None):
        self.np_random.seed(seed)

    def reset(self):
        self.initialize_environment(client.get_random_fast_lte_client_environment(), self.config.cached_urls)
        return self.observation

    def initialize_environment(self, client_environment: ClientEnvironment, cached_urls: Optional[Set[str]] = None):
        """ Initialize the environment """
        log.info(
            "initialized environment",
            network_type=client.NetworkType(client_environment.network_type),
            network_speed=client.NetworkSpeed(client_environment.network_speed),
            device_speed=client.DeviceSpeed(client_environment.device_speed),
            bandwidth=client_environment.bandwidth,
            latency=client_environment.latency,
            cpu_slowdown=client_environment.cpu_slowdown,
            loss=client_environment.loss,
            reward_func=self.analyzer.reward_func_num,
            cached_urls=cached_urls,
        )
        # Cache scenarios in hours
        scenarios = [0, 0, 0, 0, 0, 1, 2, 4, 12, 24]
        cache_time = self.np_random.choice(scenarios)
        self.cached_urls = (
            cached_urls
            if cached_urls is not None
            else set()
            if cache_time == 0
            else set(
                res.url
                for group in self.env_config.push_groups
                for res in group.resources
                if res.cache_time >= (cache_time * 60 * 60)
            )
        )

        self.client_environment = client_environment
        self.analyzer.reset(self.client_environment, self.cached_urls)

        num_domains_deployed = math.ceil(PROPORTION_DEPLOYED * len(self.env_config.push_groups))
        push_groups = sorted(self.env_config.push_groups, key=lambda g: len(g.resources), reverse=True)[
            :num_domains_deployed
        ]

        self.action_space = ActionSpace(push_groups)
        self.policy = Policy(self.action_space)

    def step(self, action: ActionIDType):
        # decode the action and apply it to the policy
        decoded_action = self.action_space.decode_action(action)
        action_applied = self.policy.apply_action(decoded_action)

        # make sure the action isn't used again
        log.info("trying action", action_id=action, action=repr(decoded_action), steps_taken=self.policy.steps_taken)
        self.action_space.use_action(decoded_action)

        reward = NOOP_ACTION_REWARD
        if action_applied:
            reward = self.analyzer.get_reward(self.policy)
            log.info("got reward", action=repr(decoded_action), reward=reward)

        info = {"action": decoded_action, "policy": self.policy.as_dict}
        return self.observation, reward, not action_applied, info

    def render(self, mode="human"):
        return super(Environment, self).render(mode=mode)

    @property
    def observation(self):
        """ Returns an observation for the current state of the environment """
        return get_observation(self.client_environment, self.env_config.push_groups, self.policy, self.cached_urls)
