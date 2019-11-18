import pytest

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment
from blaze.evaluator import Analyzer

from tests.mocks.config import get_config


class TestAnalyzer:
    def setup(self):
        self.config = get_config()
        self.policy = Policy(ActionSpace(self.config.env_config.push_groups))
        self.client_environment = get_random_client_environment()

    def get_analyzer(self, reward_func: int = 0):
        return Analyzer(get_config(), reward_func, self.client_environment)

    def test_init(self):
        a = self.get_analyzer()
        assert isinstance(a, Analyzer)
        assert a.reward_func_num == 0

    def test_init_reward_function(self):
        a0 = self.get_analyzer(0)
        assert a0.reward_func_num == 0
        a1 = self.get_analyzer(1)
        assert a1.reward_func_num == 1
        a2 = self.get_analyzer(2)
        assert a2.reward_func_num == 2
        a3 = self.get_analyzer(3)
        assert a3.reward_func_num == 3

        with pytest.raises(IndexError):
            self.get_analyzer(4)

    # TODO: REWRITE THESE TESTS

    # @mock.patch("blaze.evaluator.lighthouse.get_metrics")
    # @mock.patch("blaze.mahimahi.mahimahi.MahiMahiConfig")
    # def test_get_reward_mahimahi_config(self, mock_MahiMahiConfig, mock_get_metrics):
    #     analyzer = self.get_analyzer()
    #
    #     metrics_result = Result(speedIndex=1000)
    #     mock_get_metrics.return_value = metrics_result
    #
    #     analyzer.get_reward(self.policy)
    #     mock_MahiMahiConfig.assert_called_with(self.config, self.policy, self.client_environment)
    #
    # @mock.patch("blaze.evaluator.lighthouse.get_metrics")
    # def test_get_reward_first(self, mock_get_metrics):
    #     analyzer = self.get_analyzer()
    #
    #     metrics_result = Result(speedIndex=1000)
    #     mock_get_metrics.return_value = metrics_result
    #     reward = analyzer.get_reward(self.policy)
    #
    #     assert reward == BEST_REWARD_COEFF / metrics_result.speed_index
    #     assert analyzer.min_speed_index == metrics_result.speed_index
    #     assert analyzer.last_speed_index == metrics_result.speed_index
    #
    # @mock.patch("blaze.evaluator.lighthouse.get_metrics")
    # def test_get_reward_regression(self, mock_get_metrics):
    #     analyzer = self.get_analyzer()
    #
    #     speed_indexes = [1000, 1200]
    #     for speed_index in speed_indexes:
    #         mock_get_metrics.return_value = Result(speedIndex=speed_index)
    #         reward = analyzer.get_reward(self.policy)
    #
    #     assert reward == REGRESSION_REWARD_COEFF * (speed_indexes[1] / speed_indexes[0])
    #     assert analyzer.min_speed_index == speed_indexes[0]
    #     assert analyzer.last_speed_index == speed_indexes[1]
    #
    # @mock.patch("blaze.evaluator.lighthouse.get_metrics")
    # def test_get_reward_progression(self, mock_get_metrics):
    #     analyzer = self.get_analyzer()
    #
    #     speed_indexes = [1000, 1200, 1100]
    #     for speed_index in speed_indexes:
    #         mock_get_metrics.return_value = Result(speedIndex=speed_index)
    #         reward = analyzer.get_reward(self.policy)
    #
    #     assert reward == PROGRESSION_REWARD_COEFF * (speed_indexes[1] / speed_indexes[2])
    #     assert analyzer.min_speed_index == speed_indexes[0]
    #     assert analyzer.last_speed_index == speed_indexes[2]
    #
    # @mock.patch("blaze.evaluator.lighthouse.get_metrics")
    # def test_get_reward_new_best(self, mock_get_metrics):
    #     analyzer = self.get_analyzer()
    #
    #     speed_indexes = [1000, 1200, 1100, 900]
    #     for speed_index in speed_indexes:
    #         mock_get_metrics.return_value = Result(speedIndex=speed_index)
    #         reward = analyzer.get_reward(self.policy)
    #
    #     assert reward == BEST_REWARD_COEFF / speed_indexes[3]
    #     assert analyzer.min_speed_index == speed_indexes[3]
    #     assert analyzer.last_speed_index == speed_indexes[3]
