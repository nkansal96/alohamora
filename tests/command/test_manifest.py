import tempfile

import pytest
from unittest import mock

from blaze.chrome.har import har_from_json
from blaze.command.manifest import view_manifest
from blaze.config.environment import EnvironmentConfig
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.resource import resource_list_to_push_groups
from blaze.preprocess.url import Url

from tests.mocks.har import get_har_json


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
