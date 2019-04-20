from unittest import mock

from blaze.action import ActionSpace, Policy
from blaze.config.client import get_random_client_environment
from blaze.evaluator import Analyzer, Result
from blaze.evaluator.analyzer import BEST_REWARD_COEFF, PROGRESSION_REWARD_COEFF, REGRESSION_REWARD_COEFF

from tests.mocks.config import get_config

class TestAnalyzer():
  def setup(self):
    self.config = get_config()
    self.policy = Policy(ActionSpace(self.config.env_config.push_groups))
    self.client_environment = get_random_client_environment()

  def get_analyzer(self):
    return Analyzer(self.config, self.client_environment)

  def test_init(self):
    analyzer = self.get_analyzer()
    assert isinstance(analyzer, Analyzer)

  @mock.patch('blaze.evaluator.lighthouse.get_metrics')
  @mock.patch('blaze.mahimahi.mahimahi.MahiMahiConfig')
  def test_get_reward_mahimahi_config(self, mock_MahiMahiConfig, mock_get_metrics):
    analyzer = self.get_analyzer()

    metrics_result = Result(speedIndex=1000)
    mock_get_metrics.return_value = metrics_result

    analyzer.get_reward(self.policy)
    mock_MahiMahiConfig.assert_called_with(self.config, self.policy, self.client_environment)

  @mock.patch('blaze.evaluator.lighthouse.get_metrics')
  def test_get_reward_first(self, mock_get_metrics):
    analyzer = self.get_analyzer()

    metrics_result = Result(speedIndex=1000)
    mock_get_metrics.return_value = metrics_result
    reward = analyzer.get_reward(self.policy)

    assert reward == BEST_REWARD_COEFF/metrics_result.speed_index
    assert analyzer.min_speed_index == metrics_result.speed_index
    assert analyzer.last_speed_index == metrics_result.speed_index

  @mock.patch('blaze.evaluator.lighthouse.get_metrics')
  def test_get_reward_regression(self, mock_get_metrics):
    analyzer = self.get_analyzer()

    speed_indexes = [1000, 1200]
    for speed_index in speed_indexes:
      mock_get_metrics.return_value = Result(speedIndex=speed_index)
      reward = analyzer.get_reward(self.policy)

    assert reward == REGRESSION_REWARD_COEFF * (speed_indexes[1]/speed_indexes[0])
    assert analyzer.min_speed_index == speed_indexes[0]
    assert analyzer.last_speed_index == speed_indexes[1]

  @mock.patch('blaze.evaluator.lighthouse.get_metrics')
  def test_get_reward_progression(self, mock_get_metrics):
    analyzer = self.get_analyzer()

    speed_indexes = [1000, 1200, 1100]
    for speed_index in speed_indexes:
      mock_get_metrics.return_value = Result(speedIndex=speed_index)
      reward = analyzer.get_reward(self.policy)

    assert reward == PROGRESSION_REWARD_COEFF * (speed_indexes[1]/speed_indexes[2])
    assert analyzer.min_speed_index == speed_indexes[0]
    assert analyzer.last_speed_index == speed_indexes[2]

  @mock.patch('blaze.evaluator.lighthouse.get_metrics')
  def test_get_reward_new_best(self, mock_get_metrics):
    analyzer = self.get_analyzer()

    speed_indexes = [1000, 1200, 1100, 900]
    for speed_index in speed_indexes:
      mock_get_metrics.return_value = Result(speedIndex=speed_index)
      reward = analyzer.get_reward(self.policy)

    assert reward == BEST_REWARD_COEFF/speed_indexes[3]
    assert analyzer.min_speed_index == speed_indexes[3]
    assert analyzer.last_speed_index == speed_indexes[3]
