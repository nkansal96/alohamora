import pytest
import subprocess
import tempfile
from unittest import mock

from blaze.chrome.devtools import capture_har_in_replay_server
from blaze.chrome.har import har_from_json
from blaze.config.client import get_default_client_environment
from blaze.config.config import get_config as _get_config
from blaze.config.environment import EnvironmentConfig
from tests.mocks.har import get_har_json


class TestCaptureHarInReplayServer:
    def setup(self):
        self.client_env = get_default_client_environment()
        self.har_json = get_har_json()
        self.har = har_from_json(self.har_json)

    def test_raises_on_no_replay_dir(self):
        config = _get_config()
        with pytest.raises(ValueError):
            capture_har_in_replay_server("https://www.cs.ucla.edu", config, self.client_env)

        config = _get_config(EnvironmentConfig(request_url="https://www.cs.ucla.edu", replay_dir=""))
        with pytest.raises(ValueError):
            capture_har_in_replay_server("https://www.cs.ucla.edu", config, self.client_env)

    @mock.patch("tempfile.TemporaryDirectory")
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=get_har_json())
    @mock.patch("subprocess.run")
    def test_writes_mahimahi_files_correctly(self, mock_run, mock_open, mock_tmpdir):
        tmp_dir = "/tmp/blaze_test_123"
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        mock_tmpdir.return_value.__enter__.return_value = tmp_dir
        config = _get_config(EnvironmentConfig(request_url="https://www.cs.ucla.edu", replay_dir=tmp_dir))

        capture_har_in_replay_server("https://www.cs.ucla.edu", config, self.client_env)

        assert mock_open.call_args_list[0][0][0].startswith(tmp_dir)
        assert mock_open.call_args_list[1][0][0].startswith(tmp_dir)
        assert mock_open.call_args_list[0][0][1] == "w"
        assert mock_open.call_args_list[1][0][1] == "w"

    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=get_har_json())
    @mock.patch("subprocess.run")
    def test_calls_capture_har_with_correct_arguments(self, mock_run, mock_open):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)

        config = _get_config(EnvironmentConfig(request_url="https://www.cs.ucla.edu", replay_dir="/tmp/dir"))
        har = capture_har_in_replay_server("https://www.cs.ucla.edu", config, self.client_env)

        run_args = mock_run.call_args_list[0][0][0]
        assert run_args[0] == "docker"
        assert run_args[-1] == "https://www.cs.ucla.edu"
        assert har == self.har

    # TODO: add a real test for capture_har_in_replay_server by committing a record dir
