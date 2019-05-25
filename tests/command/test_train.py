import os
import pytest
import tempfile
from unittest import mock

from blaze.command.train import train
from blaze.config.config import get_config
from blaze.config.train import TrainConfig
from tests.mocks.config import get_env_config


class TestTrain:
    def test_train_exits_with_invalid_arguments(self):
        with pytest.raises(SystemExit):
            train([])

    def test_train_invalid_website_file(self):
        with pytest.raises(IOError):
            train(["experiment_name", "--dir", "/tmp/tmp_dir", "--manifest_file", "/non/existent/file"])

    def test_train_with_resume_and_no_resume(self):
        with pytest.raises(SystemExit):
            train(
                [
                    "experiment_name",
                    "--dir",
                    "/tmp/model_dir",
                    "--manifest_file",
                    "/tmp/manifest_file",
                    "--resume",
                    "--no-resume",
                ]
            )

    @mock.patch("blaze.model.apex.train")
    def test_train_with_non_existant_directory(self, mock_train):
        env_config = get_env_config()
        eval_dir = "/tmp/some_random_directory_that_doesnt_exist"
        train_config = TrainConfig(
            experiment_name="experiment_name", model_dir="/tmp/tmp_dir", num_cpus=4, max_timesteps=100
        )
        config = get_config(env_config, eval_dir)
        with tempfile.NamedTemporaryFile() as env_file:
            env_config.save_file(env_file.name)
            try:
                train(
                    [
                        train_config.experiment_name,
                        "--dir",
                        train_config.model_dir,
                        "--cpus",
                        str(train_config.num_cpus),
                        "--timesteps",
                        str(train_config.max_timesteps),
                        "--model",
                        "APEX",
                        "--manifest_file",
                        env_file.name,
                        "--eval_results_dir",
                        eval_dir,
                    ]
                )
                mock_train.assert_called_with(train_config, config)
            finally:
                os.rmdir(eval_dir)

    @mock.patch("blaze.model.apex.train")
    def test_train_with_existing_directory(self, mock_train):
        env_config = get_env_config()
        train_config = TrainConfig(
            experiment_name="experiment_name", model_dir="/tmp/tmp_dir", num_cpus=4, max_timesteps=100
        )
        with tempfile.NamedTemporaryFile() as env_file:
            env_config.save_file(env_file.name)
            with tempfile.TemporaryDirectory() as eval_dir:
                config = get_config(env_config, eval_dir)
                train(
                    [
                        train_config.experiment_name,
                        "--dir",
                        train_config.model_dir,
                        "--cpus",
                        str(train_config.num_cpus),
                        "--timesteps",
                        str(train_config.max_timesteps),
                        "--model",
                        "APEX",
                        "--manifest_file",
                        env_file.name,
                        "--eval_results_dir",
                        eval_dir,
                    ]
                )
                mock_train.assert_called_with(train_config, config)

    @mock.patch("blaze.model.apex.train")
    def test_train_apex(self, mock_train):
        env_config = get_env_config()
        train_config = TrainConfig(
            experiment_name="experiment_name", model_dir="/tmp/tmp_dir", num_cpus=4, max_timesteps=100
        )
        config = get_config(env_config)
        with tempfile.NamedTemporaryFile() as env_file:
            env_config.save_file(env_file.name)
            train(
                [
                    train_config.experiment_name,
                    "--dir",
                    train_config.model_dir,
                    "--cpus",
                    str(train_config.num_cpus),
                    "--timesteps",
                    str(train_config.max_timesteps),
                    "--model",
                    "APEX",
                    "--manifest_file",
                    env_file.name,
                ]
            )

        mock_train.assert_called_once()
        mock_train.assert_called_with(train_config, config)

    @mock.patch("blaze.model.ppo.train")
    def test_train_ppo(self, mock_train):
        env_config = get_env_config()
        train_config = TrainConfig(
            experiment_name="experiment_name", model_dir="/tmp/tmp_dir", num_cpus=4, max_timesteps=100
        )
        config = get_config(env_config)
        with tempfile.NamedTemporaryFile() as env_file:
            env_config.save_file(env_file.name)
            train(
                [
                    train_config.experiment_name,
                    "--dir",
                    train_config.model_dir,
                    "--cpus",
                    str(train_config.num_cpus),
                    "--timesteps",
                    str(train_config.max_timesteps),
                    "--model",
                    "PPO",
                    "--manifest_file",
                    env_file.name,
                ]
            )

        mock_train.assert_called_once()
        mock_train.assert_called_with(train_config, config)

    @mock.patch("blaze.model.apex.train")
    def test_train_resume(self, mock_train):
        env_config = get_env_config()
        train_config = TrainConfig(
            experiment_name="experiment_name", model_dir="/tmp/tmp_dir", num_cpus=4, max_timesteps=100, resume=True
        )
        config = get_config(env_config)
        with tempfile.NamedTemporaryFile() as env_file:
            env_config.save_file(env_file.name)
            train(
                [
                    train_config.experiment_name,
                    "--dir",
                    train_config.model_dir,
                    "--cpus",
                    str(train_config.num_cpus),
                    "--timesteps",
                    str(train_config.max_timesteps),
                    "--model",
                    "APEX",
                    "--manifest_file",
                    env_file.name,
                    "--resume",
                ]
            )

        mock_train.assert_called_once()
        mock_train.assert_called_with(train_config, config)

    @mock.patch("blaze.model.apex.train")
    def test_train_no_resume(self, mock_train):
        env_config = get_env_config()
        train_config = TrainConfig(
            experiment_name="experiment_name", model_dir="/tmp/tmp_dir", num_cpus=4, max_timesteps=100, resume=False
        )
        config = get_config(env_config)
        with tempfile.NamedTemporaryFile() as env_file:
            env_config.save_file(env_file.name)
            train(
                [
                    train_config.experiment_name,
                    "--dir",
                    train_config.model_dir,
                    "--cpus",
                    str(train_config.num_cpus),
                    "--timesteps",
                    str(train_config.max_timesteps),
                    "--model",
                    "APEX",
                    "--manifest_file",
                    env_file.name,
                    "--no-resume",
                ]
            )

        mock_train.assert_called_once()
        mock_train.assert_called_with(train_config, config)
