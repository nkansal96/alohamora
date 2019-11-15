"""
This module defines the analyzer which tests a push policy by loading the page
under the specified circumstances and returns a metric indicating the policy
quality
"""

from typing import Optional

from blaze.action import Policy
from blaze.config import client, Config
from blaze.evaluator import simulator
from blaze.logger import logger

# from blaze.mahimahi import mahimahi

MIN_PAGE_LOAD_TIME = 1000000.0
BEST_REWARD_COEFF = 200000.0
REGRESSION_REWARD_COEFF = -5.0
PROGRESSION_REWARD_COEFF = 10.0


class Analyzer:
    """
    Analyzer loads a page with some push policy in a configured client environment
    and evaluates how good the policy is. The reward is based on the speed index
    metric and considers whether the push policy produced the best speed index so far,
    a better speed index than the previous policy, or a worse speed index than the
    previous policy
    """

    def __init__(
        self, config: Config, reward_func: int = 0, client_environment: Optional[client.ClientEnvironment] = None
    ):
        self.config = config
        self.client_environment = client_environment
        self.simulator = simulator.Simulator(config.env_config)
        self.last_plt = 0
        self.min_plt = MIN_PAGE_LOAD_TIME
        self.reward_func = {0: self._reward_0, 1: self._reward_1, 2: self._reward_2, 3: self._reward_3}[reward_func]
        self.log = logger.with_namespace("analyzer")

    def reset(self, client_environment: Optional[client.ClientEnvironment] = None):
        """ Resets the analyzer's state and optionally changes the client environment """
        self.last_plt = 0
        self.min_plt = MIN_PAGE_LOAD_TIME
        self.client_environment = client_environment or self.client_environment

    def get_reward(self, policy: Policy) -> float:
        """
        Evaluates the given push policy by instantiating a Mahimahi environment simulating
        the client environment and the page load.
        """
        return self.reward_func(policy)

    def _reward_0(self, policy: Policy) -> float:
        plt = self.simulator.simulate_load_time(self.client_environment, policy)
        if self.last_plt == 0:
            reward = 1000000.0 * (1.0 / plt)
        else:
            reward = 1000000.0 * (1.0 / plt - 1.0 / self.last_plt)
        self.last_plt = plt
        return reward

    def _reward_1(self, policy: Policy) -> float:
        plt = self.simulator.simulate_load_time(self.client_environment, policy)
        return 1.0 / plt

    def _reward_2(self, policy: Policy) -> float:
        plt = self.simulator.simulate_load_time(self.client_environment, policy)
        return -plt

    def _reward_3(self, policy: Policy) -> float:
        plt = self.simulator.simulate_load_time(self.client_environment, policy)
        if plt < self.min_plt:
            reward = BEST_REWARD_COEFF / plt
        else:
            a, b = sorted([plt, self.last_plt])
            coeff = REGRESSION_REWARD_COEFF if plt > self.last_plt else PROGRESSION_REWARD_COEFF
            reward = coeff * (b / a)
        self.min_plt = min(self.min_plt, plt)
        self.last_plt = plt
        return reward
