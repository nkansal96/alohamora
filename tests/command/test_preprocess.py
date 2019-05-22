import tempfile

import pytest
from unittest import mock

from blaze.command.preprocess import preprocess, view_manifest
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.record import STABLE_SET_NUM_RUNS
from blaze.preprocess.resource import resource_list_to_push_groups
from blaze.preprocess.url import Url

from tests.mocks.har import generate_har, HarReturner

class TestPreprocess():
  def test_exits_with_missing_arguments(self):
    with pytest.raises(SystemExit):
      preprocess([])

  @mock.patch('blaze.command.preprocess.record_webpage')
  def test_runs_successfully(self, mock_record_webpage):
    hars = [generate_har() for _ in range(STABLE_SET_NUM_RUNS)]
    with tempfile.NamedTemporaryFile() as output_file:
      with tempfile.TemporaryDirectory() as output_dir:
        with mock.patch('blaze.preprocess.record.capture_har', new=HarReturner(hars)):
          preprocess([
            'http://cs.ucla.edu',
            '--output', output_file.name,
            '--record_dir', output_dir,
          ])

        config = EnvironmentConfig.load_file(output_file.name)
        assert config.replay_dir == output_dir
        assert config.request_url == 'http://cs.ucla.edu'
        assert config.push_groups
        # since we passed cs.ucla.edu as URL, nothing should be trainable
        assert all(not group.trainable for group in config.push_groups)

    mock_record_webpage.assert_called_once()
    mock_record_webpage.assert_called_with('http://cs.ucla.edu', output_dir, get_config())

  @mock.patch('blaze.command.preprocess.record_webpage')
  def test_runs_successfully_with_train_domain_suffix(self, mock_record_webpage):
    hars = [generate_har() for _ in range(STABLE_SET_NUM_RUNS)]
    with tempfile.NamedTemporaryFile() as output_file:
      with tempfile.TemporaryDirectory() as output_dir:
        with mock.patch('blaze.preprocess.record.capture_har', new=HarReturner(hars)):
          preprocess([
            'http://cs.ucla.edu',
            '--output', output_file.name,
            '--record_dir', output_dir,
            '--train_domain_globs', '*reddit.com',
          ])

        config = EnvironmentConfig.load_file(output_file.name)
        assert config.replay_dir == output_dir
        assert config.request_url == 'http://cs.ucla.edu'
        assert config.push_groups
        # since we passed reddit.com as train_domain_suffix, something should be trainable
        assert any(group.trainable for group in config.push_groups)

    mock_record_webpage.assert_called_once()
    mock_record_webpage.assert_called_with('http://cs.ucla.edu', output_dir, get_config())

class TestViewManifest():
  def test_view_manifest_exits_with_missing_arguments(self):
    with pytest.raises(SystemExit):
      view_manifest([])

  def test_view_manifest(self):
    har = generate_har()
    res_list = har_entries_to_resources(har.log.entries)
    push_groups = resource_list_to_push_groups(res_list)
    config = EnvironmentConfig(
      request_url='http://cs.ucla.edu/',
      replay_dir='/tmp/tmp_dir',
      push_groups=push_groups,
    )
    with mock.patch('builtins.print') as mock_print:
      with tempfile.NamedTemporaryFile() as config_file:
        config.save_file(config_file.name)
        view_manifest([config_file.name])
    assert mock_print.call_count > 5

    printed_text = '\n'.join(call[0][0] for call in mock_print.call_args_list if call[0])
    assert config.replay_dir in printed_text
    assert config.request_url in printed_text
    assert all(group.name in printed_text for group in config.push_groups)
    assert all(Url.parse(res.url).resource[:61] in printed_text
               for group in config.push_groups
               for res in group.resources)
