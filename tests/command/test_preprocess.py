import tempfile

import pytest
from unittest import mock

from blaze.chrome.har import har_from_json
from blaze.command.preprocess import preprocess, record, view_manifest
from blaze.config.client import get_default_client_environment
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.record import STABLE_SET_NUM_RUNS
from blaze.preprocess.resource import resource_list_to_push_groups
from blaze.preprocess.url import Url

from tests.mocks.har import generate_har, get_har_json, HarReturner


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

    @mock.patch("blaze.command.preprocess.capture_har_in_mahimahi")
    def test_runs_successfully(self, mock_capture_har_in_mahimahi):
        hars = [generate_har() for _ in range(STABLE_SET_NUM_RUNS + 1)]
        har_resources = har_entries_to_resources(hars[0])
        mock_capture_har_in_mahimahi.return_value = hars[0]
        with tempfile.NamedTemporaryFile() as output_file:
            with tempfile.TemporaryDirectory() as output_dir:
                with mock.patch("blaze.preprocess.record.capture_har_in_mahimahi", new=HarReturner(hars)):
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

    @mock.patch("blaze.command.preprocess.capture_har_in_mahimahi")
    def test_runs_successfully_with_train_domain_suffix(self, mock_capture_har_in_mahimahi):
        hars = [generate_har() for _ in range(STABLE_SET_NUM_RUNS + 1)]
        har_resources = har_entries_to_resources(hars[0])
        mock_capture_har_in_mahimahi.return_value = hars[0]
        with tempfile.NamedTemporaryFile() as output_file:
            with tempfile.TemporaryDirectory() as output_dir:
                with mock.patch("blaze.preprocess.record.capture_har_in_mahimahi", new=HarReturner(hars)):
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


class TestViewManifest:
    def test_view_manifest_exits_with_missing_arguments(self):
        with pytest.raises(SystemExit):
            view_manifest([])

    def test_view_manifest(self):
        har = har_from_json(get_har_json())
        res_list = har_entries_to_resources(har)
        push_groups = resource_list_to_push_groups(res_list)
        config = EnvironmentConfig(
            replay_dir="", request_url="https://www.reddit.com/", push_groups=push_groups, har_resources=res_list
        )

        with mock.patch("builtins.print") as mock_print:
            with tempfile.NamedTemporaryFile() as config_file:
                config.save_file(config_file.name)
                view_manifest([config_file.name])
        assert mock_print.call_count > 5

        printed_text = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        assert config.replay_dir in printed_text
        assert config.request_url in printed_text
        assert all(group.name in printed_text for group in config.push_groups)
        assert all(
            Url.parse(res.url).resource[:61] in printed_text for group in config.push_groups for res in group.resources
        )

    def test_view_manifest_only_trainable(self):
        json = get_har_json()
        har = har_from_json(json)
        res_list = har_entries_to_resources(har)
        push_groups = resource_list_to_push_groups(res_list, train_domain_globs=["*reddit.com"])
        config = EnvironmentConfig(
            replay_dir="", request_url="https://www.reddit.com/", push_groups=push_groups, har_resources=res_list
        )
        with mock.patch("builtins.print") as mock_print:
            with tempfile.NamedTemporaryFile() as config_file:
                config.save_file(config_file.name)
                view_manifest(["--trainable", config_file.name])
        assert mock_print.call_count > 5

        printed_text = "\n".join(call[0][0] for call in mock_print.call_args_list if call[0])
        assert config.replay_dir in printed_text
        assert config.request_url in printed_text
        assert all(group.name in printed_text for group in config.push_groups if group.trainable)

        pre_graph_text = printed_text.split("Execution Graph")[0]
        assert not any(group.name in pre_graph_text for group in config.push_groups if not group.trainable)
