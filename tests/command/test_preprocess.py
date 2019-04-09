import os
import pytest
import tempfile
from unittest import mock

from blaze.command.preprocess import preprocess
from blaze.config.config import get_config
from blaze.config.environment import EnvironmentConfig
from blaze.preprocess.record import STABLE_SET_NUM_RUNS
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

    mock_record_webpage.assert_called_once()
    mock_record_webpage.assert_called_with('http://cs.ucla.edu', output_dir, get_config())
