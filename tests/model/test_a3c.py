from ray.rllib.agents.dqn import ApexAgent

from unittest import mock
from blaze.config.config import get_config
from blaze.environment import Environment
from blaze.model import apex
from blaze.model.model import SavedModel
from tests.mocks.config import get_env_config, get_train_config


class TestApex:
    @mock.patch("ray.init")
    @mock.patch("ray.tune.run_experiments")
    def test_train_compiles(self, mock_run_experiments, _):
        apex.train(get_train_config(), get_config(get_env_config()))
        mock_run_experiments.assert_called_once()

    def test_get_model(self):
        location = "/tmp/model_location"
        saved_model = apex.get_model(location)
        assert isinstance(saved_model, SavedModel)
        assert saved_model.cls is ApexAgent
        assert saved_model.env is Environment
        assert saved_model.location == location
