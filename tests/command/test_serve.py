import pytest
import tempfile
from unittest import mock

from ray.rllib.agents.dqn import ApexAgent
from ray.rllib.agents.ppo import PPOAgent

from blaze.command.serve import serve
from blaze.config.config import get_config
from blaze.config.train import TrainConfig
from tests.mocks.config import get_env_config
from tests.mocks.serve import MockServer

class TestServe():
  def test_serve_exits_with_invalid_arguments(self):
    with pytest.raises(SystemExit):
      serve([])

  def test_serve_invalid_model_location(self):
    with pytest.raises(IOError):
      serve(['--model', 'APEX', '/non/existent/dir'])

  @mock.patch('time.sleep')
  def test_serve_apex(self, mock_sleep):
    mock_sleep.side_effect = KeyboardInterrupt()
    with mock.patch('blaze.serve.server.Server', new=MockServer()) as mock_server:
      with tempfile.TemporaryDirectory() as model_location:
        serve([
          '--model', 'APEX',
          '--port', '5678',
          '--host', '127.0.0.1',
          '--max_workers', '16',
          model_location,
        ])

    assert mock_server.args[0].host == '127.0.0.1'
    assert mock_server.args[0].port == 5678
    assert mock_server.args[0].max_workers == 16
    assert mock_server.set_policy_service_args[0].saved_model.cls == ApexAgent
    assert mock_server.set_policy_service_args[0].saved_model.location == model_location
    assert mock_server.start_called
    assert mock_server.stop_called

  @mock.patch('time.sleep')
  def test_serve_ppo(self, mock_sleep):
    mock_sleep.side_effect = KeyboardInterrupt()
    with mock.patch('blaze.serve.server.Server', new=MockServer()) as mock_server:
      with tempfile.TemporaryDirectory() as model_location:
        serve([
          '--model', 'PPO',
          '--port', '5678',
          '--host', '127.0.0.1',
          '--max_workers', '16',
          model_location,
        ])

    assert mock_server.args[0].host == '127.0.0.1'
    assert mock_server.args[0].port == 5678
    assert mock_server.args[0].max_workers == 16
    assert mock_server.set_policy_service_args[0].saved_model.cls == PPOAgent
    assert mock_server.set_policy_service_args[0].saved_model.location == model_location
    assert mock_server.start_called
    assert mock_server.stop_called
