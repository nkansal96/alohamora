from unittest import mock
from blaze.config.config import get_config
from blaze.model import ppo
from tests.mocks.config import get_env_config, get_train_config

class TestPPO(): 
  @mock.patch('ray.init')
  @mock.patch('ray.tune.run_experiments')
  def test_train_compiles(self, mock_run_experiments, _):
    ppo.train(get_train_config(), get_config(get_env_config()))
    mock_run_experiments.assert_called_once()
