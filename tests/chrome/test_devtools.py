import pytest
import subprocess
import tempfile
from unittest import mock

from blaze.chrome.devtools import capture_har, capture_har_in_mahimahi
from blaze.chrome.har import har_from_json
from blaze.config.client import get_default_client_environment
from blaze.config.config import get_config as _get_config
from blaze.config.environment import EnvironmentConfig
from tests.mocks.config import get_config
from tests.mocks.har import get_har_json


class TestCaptureHar:
    def setup(self):
        self.config = get_config()
        self.har_json = get_har_json()
        self.har = har_from_json(self.har_json)

    @mock.patch("time.sleep")
    @mock.patch("subprocess.run")
    def test_correct_proc_flags(self, mock_run, _):
        mock_run.return_value.stdout = self.har_json
        url = "https://www.google.com"
        capture_har(url, self.config)

        mock_run.assert_called_once()

        har_capturer_args = mock_run.call_args[0][0]
        assert har_capturer_args[0] == self.config.chrome_har_capturer_bin
        assert har_capturer_args[-1] == url

    @mock.patch("time.sleep")
    @mock.patch("subprocess.run")
    def test_capture_har(self, mock_run, _):
        mock_run.return_value.stdout = self.har_json
        url = "https://www.google.com"
        har = capture_har(url, self.config)

        mock_run.assert_called_once()
        assert har
        assert har.log.entries
        assert har.timings
        assert len(har.log.entries) == len(self.har.log.entries)
        assert len(har.timings) == len(self.har.timings)

    def test_capture_har_for_real(self, is_ci):
        # don't perform this test in CI since it's currently a pain
        if is_ci:
            assert True
            return
        # perform a real run through of capture_har on a small webpage
        url = "https://varvy.com/pagespeed/wicked-fast.html"
        har = capture_har(url, self.config)
        assert har.log.entries
        assert har.timings
        assert har.log.entries[0].request.url == url

    def test_capture_har_for_real_to_file(self, is_ci):
        # don't perform this test in CI since it's currently a pain
        if is_ci:
            assert True
            return

        # perform a real run through of capture_har on a small webpage
        url = "https://varvy.com/pagespeed/wicked-fast.html"
        with tempfile.NamedTemporaryFile() as output_file:
            har = capture_har(url, self.config, output_filepath=output_file.name)
            assert har.log.entries
            assert har.timings
            assert har.log.entries[0].request.url == url


class TestCaptureHarInMahimahi:
    def setup(self):
        self.client_env = get_default_client_environment()
        self.har_json = get_har_json()
        self.har = har_from_json(self.har_json)

    def test_raises_on_no_replay_dir(self):
        config = _get_config()
        with pytest.raises(ValueError):
            capture_har_in_mahimahi("https://www.cs.ucla.edu", config, self.client_env)

        config = _get_config(EnvironmentConfig(request_url="https://www.cs.ucla.edu", replay_dir=""))
        with pytest.raises(ValueError):
            capture_har_in_mahimahi("https://www.cs.ucla.edu", config, self.client_env)

    @mock.patch("tempfile.TemporaryDirectory")
    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=get_har_json())
    @mock.patch("subprocess.run")
    def test_writes_mahimahi_files_correctly(self, mock_run, mock_open, mock_tmpdir):
        tmp_dir = "/tmp/blaze_test_123"
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)
        mock_tmpdir.return_value.__enter__.return_value = tmp_dir
        config = _get_config(EnvironmentConfig(request_url="https://www.cs.ucla.edu", replay_dir=tmp_dir))

        capture_har_in_mahimahi("https://www.cs.ucla.edu", config, self.client_env)

        assert mock_open.call_args_list[0][0][0].startswith(tmp_dir)
        assert mock_open.call_args_list[1][0][0].startswith(tmp_dir)
        assert mock_open.call_args_list[0][0][1] == "w"
        assert mock_open.call_args_list[1][0][1] == "w"

    @mock.patch("builtins.open", new_callable=mock.mock_open, read_data=get_har_json())
    @mock.patch("subprocess.run")
    def test_calls_capture_har_with_correct_arguments(self, mock_run, mock_open):
        mock_run.return_value = subprocess.CompletedProcess(args=[], returncode=0)

        config = _get_config(EnvironmentConfig(request_url="https://www.cs.ucla.edu", replay_dir="/tmp/dir"))
        har = capture_har_in_mahimahi("https://www.cs.ucla.edu", config, self.client_env)

        run_args = mock_run.call_args_list[0][0][0]
        assert run_args[0] == "mm-proxyreplay"
        assert run_args[-5].endswith("capture_har.js")
        assert run_args[-3] == "https://www.cs.ucla.edu"
        assert har == self.har
