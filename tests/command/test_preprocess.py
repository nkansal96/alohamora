import tempfile

import pytest
from unittest import mock

from blaze.command.preprocess import preprocess, record
from blaze.config.client import get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.record import STABLE_SET_NUM_RUNS

from tests.mocks.har import generate_har, HarReturner


class TestRecord:
    def test_exits_with_missing_arguments(self):
        with pytest.raises(SystemExit):
            record([])

    @mock.patch("blaze.command.preprocess.record_webpage")
    def test_runs_successfully(self, record_webpage):
        with tempfile.TemporaryDirectory() as record_dir:
            record(["https://cs.ucla.edu", "--record_dir", record_dir])


class TestPreprocess:
    def test_exits_with_missing_arguments(self):
        with pytest.raises(SystemExit):
            preprocess([])

    @mock.patch("blaze.command.preprocess.capture_har_in_replay_server")
    def test_runs_successfully(self, mock_capture_har_in_mahimahi):
        hars = [generate_har() for _ in range(STABLE_SET_NUM_RUNS + 1)]
        har_resources = har_entries_to_resources(hars[0])
        mock_capture_har_in_mahimahi.return_value = hars[0]
        with tempfile.NamedTemporaryFile() as output_file:
            with tempfile.TemporaryDirectory() as output_dir:
                with mock.patch("blaze.preprocess.record.capture_har_in_replay_server", new=HarReturner(hars)):
                    preprocess(["https://cs.ucla.edu", "--output", output_file.name, "--record_dir", output_dir])

                config = EnvironmentConfig.load_file(output_file.name)
                assert config.replay_dir == output_dir
                assert config.request_url == "https://cs.ucla.edu"
                assert config.push_groups
                # since we passed cs.ucla.edu as URL, nothing should be trainable
                assert all(not group.trainable for group in config.push_groups)
                assert config.har_resources == har_resources

        client_env = get_default_client_environment()
        config = get_config(EnvironmentConfig(replay_dir=output_dir, request_url="https://cs.ucla.edu"))

        mock_capture_har_in_mahimahi.assert_called_once()
        mock_capture_har_in_mahimahi.assert_called_with("https://cs.ucla.edu", config, client_env)

    @mock.patch("blaze.command.preprocess.capture_har_in_replay_server")
    def test_runs_successfully_with_train_domain_suffix(self, mock_capture_har_in_mahimahi):
        hars = [generate_har() for _ in range(STABLE_SET_NUM_RUNS + 1)]
        har_resources = har_entries_to_resources(hars[0])
        mock_capture_har_in_mahimahi.return_value = hars[0]
        with tempfile.NamedTemporaryFile() as output_file:
            with tempfile.TemporaryDirectory() as output_dir:
                with mock.patch("blaze.preprocess.record.capture_har_in_replay_server", new=HarReturner(hars)):
                    preprocess(
                        [
                            "https://cs.ucla.edu",
                            "--output",
                            output_file.name,
                            "--record_dir",
                            output_dir,
                            "--train_domain_globs",
                            "*reddit.com",
                        ]
                    )

                config = EnvironmentConfig.load_file(output_file.name)
                assert config.replay_dir == output_dir
                assert config.request_url == "https://cs.ucla.edu"
                assert config.push_groups
                # since we passed reddit.com as train_domain_suffix, something should be trainable
                assert any(group.trainable for group in config.push_groups)
                assert config.har_resources == har_resources

        client_env = get_default_client_environment()
        config = get_config(EnvironmentConfig(replay_dir=output_dir, request_url="https://cs.ucla.edu"))

        mock_capture_har_in_mahimahi.assert_called_once()
        mock_capture_har_in_mahimahi.assert_called_with("https://cs.ucla.edu", config, client_env)
