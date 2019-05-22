import pytest
import subprocess
from unittest import mock

from blaze.chrome.har import har_from_json
from blaze.chrome.devtools import capture_har, REMOTE_DEBUGGING_PORT
from tests.mocks.config import get_config
from tests.mocks.har import get_har_json


class TestCaptureHar:
    def setup(self):
        self.config = get_config()
        self.har_json = get_har_json()
        self.har = har_from_json(self.har_json)

    @mock.patch("time.sleep")
    @mock.patch("subprocess.Popen")
    @mock.patch("subprocess.run")
    def test_correct_proc_flags(self, mock_run, mock_popen, _):
        mock_run.return_value.stdout = self.har_json
        url = "https://www.google.com"
        har = capture_har(url, self.config)

        mock_popen.assert_called_once()
        mock_run.assert_called_once()

        chrome_args = mock_popen.call_args[0][0]
        assert chrome_args[0] == self.config.chrome_bin
        assert any("remote-debugging-port={}".format(REMOTE_DEBUGGING_PORT) in flag for flag in chrome_args)
        assert any("user-data-dir=/" in flag for flag in chrome_args)

        har_capturer_args = mock_run.call_args[0][0]
        assert har_capturer_args[0] == self.config.chrome_har_capturer_bin
        assert har_capturer_args[-1] == url
        assert any(str(REMOTE_DEBUGGING_PORT) == flag for flag in har_capturer_args)

    @mock.patch("time.sleep")
    @mock.patch("subprocess.Popen")
    @mock.patch("subprocess.run")
    def test_terminates_chrome_if_har_capturer_raises(self, mock_run, mock_popen, _):
        mock_run.return_value.check_returncode.side_effect = subprocess.CalledProcessError(returncode=1, cmd=[])
        with pytest.raises(subprocess.CalledProcessError):
            url = "https://www.google.com"
            capture_har(url, self.config)
        mock_popen.return_value.terminate.assert_called_once()

    @mock.patch("time.sleep")
    @mock.patch("subprocess.Popen")
    @mock.patch("subprocess.run")
    def test_capture_har(self, mock_run, mock_popen, _):
        mock_run.return_value.stdout = self.har_json
        url = "https://www.google.com"
        har = capture_har(url, self.config)

        mock_popen.assert_called_once()
        mock_run.assert_called_once()
        assert har
        assert har.log.entries
        assert len(har.log.entries) == len(self.har.log.entries)

    def test_capture_har_for_real(self, is_ci):
        # don't perform this test in CI since it's currently a pain
        if is_ci:
            assert True
            return
        # perform a real run through of capture_har on a small webpage
        url = "https://varvy.com/pagespeed/wicked-fast.html"
        har = capture_har(url, self.config)
        assert len(har.log.entries) > 1
        assert har.log.entries[0].request.url == url
