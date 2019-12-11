"""
This module defines the analyzer which tests a push policy by loading the page
under the specified circumstances and returns a metric indicating the policy
quality
"""

from typing import Callable, List, Optional, Set

from blaze.action import Policy
from blaze.config.client import ClientEnvironment
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Simulator
from blaze.logger import logger

# Define the call signature of a reward function
# (simulator, client environment, cached urls) => ((policy) => float)
RewardFunction = Callable[[Simulator, ClientEnvironment, Set[str], Optional[bool]], Callable[[Policy], float]]

MIN_PAGE_LOAD_TIME = 1000000.0
BEST_REWARD_COEFF = 200000.0
REGRESSION_REWARD_COEFF = -5.0
PROGRESSION_REWARD_COEFF = 5.0


def reward_0(
    simulator: Simulator, client_environment: ClientEnvironment, cached_urls: Set[str], use_aft: bool = False
) -> Callable[[Policy], float]:
    """
    Returns a reward function that returns the difference in 1/plt and 1/last_plt
    """
    last_plt = 0

    def _reward(policy: Policy) -> float:
        nonlocal last_plt

        plt = simulator.simulate_load_time(client_environment, policy=policy, cached_urls=cached_urls, use_aft=use_aft)
        if last_plt == 0:
            reward = 1000000.0 * (1.0 / plt)
        else:
            reward = 1000000.0 * (1.0 / plt - 1.0 / last_plt)
        last_plt = plt
        return reward

    return _reward


def reward_1(
    simulator: Simulator, client_environment: ClientEnvironment, cached_urls: Set[str], use_aft: bool = False
) -> Callable[[Policy], float]:
    """
    Returns a reward function that returns 1/plt
    """

    def _reward(policy: Policy) -> float:
        plt = simulator.simulate_load_time(client_environment, policy=policy, cached_urls=cached_urls, use_aft=use_aft)
        return 1000000.0 / plt

    return _reward


def reward_2(
    simulator: Simulator, client_environment: ClientEnvironment, cached_urls: Set[str], use_aft: bool = False
) -> Callable[[Policy], float]:
    """
    Returns a reward function that returns -plt
    """

    def _reward(policy: Policy) -> float:
        plt = simulator.simulate_load_time(client_environment, policy=policy, cached_urls=cached_urls, use_aft=use_aft)
        return -plt

    return _reward


def reward_3(
    simulator: Simulator, client_environment: ClientEnvironment, cached_urls: Set[str], use_aft: bool = False
) -> Callable[[Policy], float]:
    """
    Returns a reward function that returns the original 3-part reward
    """
    min_plt = simulator.simulate_load_time(client_environment) if client_environment else MIN_PAGE_LOAD_TIME
    last_plt = min_plt if min_plt < MIN_PAGE_LOAD_TIME else 0

    def _reward(policy: Policy) -> float:
        nonlocal min_plt, last_plt

        plt = simulator.simulate_load_time(client_environment, policy=policy, cached_urls=cached_urls, use_aft=use_aft)
        if plt < min_plt:
            reward = BEST_REWARD_COEFF / plt
        else:
            a, b = sorted([plt, last_plt])
            coeff = REGRESSION_REWARD_COEFF if plt > last_plt else PROGRESSION_REWARD_COEFF
            reward = coeff * (b / a)
        min_plt = min(min_plt, plt)
        last_plt = plt
        return reward

    return _reward


REWARD_FUNCTIONS: List[RewardFunction] = [reward_0, reward_1, reward_2, reward_3]


def get_num_rewards():
    """ Returns the number of reward functions """
    return len(REWARD_FUNCTIONS)


class Analyzer:
    """
    Analyzer loads a page with some push policy in a configured client environment
    and evaluates how good the policy is. The reward is based on the speed index
    metric and considers whether the push policy produced the best speed index so far,
    a better speed index than the previous policy, or a worse speed index than the
    previous policy
    """

    def __init__(
        self,
        env_config: EnvironmentConfig,
        reward_func_num: int = 0,
        use_aft: bool = False,
        client_environment: Optional[ClientEnvironment] = None,
        cached_urls: Optional[Set[str]] = None,
    ):
        self.env_config = env_config
        self.use_aft = use_aft
        self.cached_urls = cached_urls
        self.client_environment = client_environment
        self.simulator = Simulator(env_config)
        self.reward_func_num = reward_func_num
        self.reward_func = REWARD_FUNCTIONS[self.reward_func_num](
            self.simulator, self.client_environment, self.cached_urls, self.use_aft
        )
        self.log = logger.with_namespace("analyzer")

    def reset(
        self,
        env_config: Optional[EnvironmentConfig] = None,
        client_environment: Optional[ClientEnvironment] = None,
        cached_urls: Optional[Set[str]] = None,
    ):
        """ Resets the analyzer's state and optionally changes the client environment """
        self.env_config = env_config or self.env_config
        self.client_environment = client_environment or self.client_environment
        self.cached_urls = cached_urls
        self.simulator = Simulator(self.env_config)
        self.reward_func = REWARD_FUNCTIONS[self.reward_func_num](
            self.simulator, self.client_environment, self.cached_urls, self.use_aft
        )

    def get_reward(self, policy: Policy) -> float:
        """
        Evaluates the given push policy by instantiating a Mahimahi environment simulating
        the client environment and the page load.
        """
        return self.reward_func(policy)
