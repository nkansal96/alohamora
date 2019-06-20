"""
This module defines the analyzer which tests a push policy by loading the page
under the specified circumstances and returns a metric indicating the policy
quality
"""

import json
import os
import tempfile
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
        self.min_plt = MIN_PAGE_LOAD_TIME
        self.last_plt = None
        self.simulator = simulator.Simulator(config.env_config)
        self.log = logger.with_namespace("analyzer")

    def reset(self, client_environment: Optional[client.ClientEnvironment] = None):
        """ Resets the analyzer's state and optionally changes the client environment """
        self.client_environment = client_environment or self.client_environment
        self.min_plt = MIN_PAGE_LOAD_TIME
        self.last_plt = None

    def get_reward(self, policy: Policy):
        """
        Evaluates the given push policy by instantiating a Mahimahi environment simulating
        the client environment and the page load. It calculates the reward based on the
        resulting speed index returned from Lighthouse
        """
        self.log.debug("analyzing web page...")
        # mm_config = mahimahi.MahiMahiConfig(self.config, policy, self.client_environment)
        # metrics = lighthouse.get_metrics(self.config, mm_config)
        # speed_index = float(metrics.speed_index)
        plt = self.simulator.simulate_load_time(self.client_environment, policy)
        reward = 0
        if plt < self.min_plt:
            self.log.debug("received best page load time", plt=plt)
            reward = BEST_REWARD_COEFF / plt
        else:
            a, b = sorted([plt, self.last_plt])
            sign = REGRESSION_REWARD_COEFF if plt > self.last_plt else PROGRESSION_REWARD_COEFF
            self.log.debug("received {} page load time".format("better" if sign > 0 else "worse"), plt=plt)
            reward = sign * (b / a)
        self.min_plt = min(self.min_plt, plt)
        self.last_plt = plt
        self.write_eval_result(plt, policy)
        return reward

    def write_eval_result(self, speed_index: float, policy: Policy):
        """
        Writes a JSON file to the configured eval_results_dir that contains some debugging information
        about the Lighthouse evaluation result
        """
        dirname = self.config.eval_results_dir
        if not dirname or not os.path.isdir(dirname):
            self.log.debug("skipping write_eval_result due to invalid eval_results_dir", eval_results_dir=dirname)
            return
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", dir=dirname, delete=False) as f:
            json.dump(
                {
                    "url": self.config.env_config.request_url,
                    "speed_index": speed_index,
                    "policy": policy.as_dict,
                    "client_environment": self.client_environment._asdict(),
                },
                f.file,
                indent=2,
            )
            self.log.debug("wrote eval result", url=self.config.env_config.request_url, path=f.name)
