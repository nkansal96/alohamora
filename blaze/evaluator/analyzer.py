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
REGRESSION_REWARD_COEFF = -2.0
PROGRESSION_REWARD_COEFF = 4.0


class Analyzer:
    """
    Analyzer loads a page with some push policy in a configured client environment
    and evaluates how good the policy is. The reward is based on the speed index
    metric and considers whether the push policy produced the best speed index so far,
    a better speed index than the previous policy, or a worse speed index than the
    previous policy
    """

    def __init__(self, config: Config, client_environment: Optional[client.ClientEnvironment] = None):
        self.config = config
        self.client_environment = client_environment
        self.simulator = simulator.Simulator(config.env_config)
        self.log = logger.with_namespace("analyzer")

    def reset(self, client_environment: Optional[client.ClientEnvironment] = None):
        """ Resets the analyzer's state and optionally changes the client environment """
        self.client_environment = client_environment or self.client_environment

    def get_reward(self, policy: Policy):
        """
        Evaluates the given push policy by instantiating a Mahimahi environment simulating
        the client environment and the page load. It calculates the reward based on the
        resulting speed index returned from Lighthouse
        """
        plt = self.simulator.simulate_load_time(self.client_environment, policy)
        self.log.debug("got page load time", plt=plt, reward=-plt)
        return -plt
