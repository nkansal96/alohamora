import pytest
from unittest import mock

from blaze.chrome.har import har_from_json
from blaze.command.analyze import page_load_time
from blaze.config.client import get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig

from tests.mocks.har import get_har_json


class TestPageLoadTime:
    def test_page_load_time_raises_without_url(self):
        with pytest.raises(SystemExit):
            page_load_time([])

    # TODO: redo these tests
    # @mock.patch("os.rmdir")
    # @mock.patch("blaze.command.analyze.record_webpage")
    # @mock.patch("blaze.command.analyze.capture_har_in_replay_server")
    # def test_page_load_time(self, mock_capture_har_in_mahimahi, mock_record_webpage, mock_rmdir):
    #     mock_capture_har_in_mahimahi.return_value = har_from_json(get_har_json())
    #     url = "https://www.reddit.com/"
    #     page_load_time([url])
    #
    #     record_webpage_args = mock_record_webpage.call_args_list[0][0]
    #     client_env = get_default_client_environment()
    #     config = get_config(EnvironmentConfig(replay_dir=record_webpage_args[1], request_url=url))
    #     assert record_webpage_args[0] == url
    #     assert record_webpage_args[1]
    #     assert record_webpage_args[2] == config
    #
    #     capture_har_in_mahimahi_args = mock_capture_har_in_mahimahi.call_args_list[0][0]
    #     assert capture_har_in_mahimahi_args[0] == url
    #     assert capture_har_in_mahimahi_args[1] == config
    #     assert capture_har_in_mahimahi_args[2] == client_env
    #
    #     mock_rmdir.assert_called_with(record_webpage_args[1])
