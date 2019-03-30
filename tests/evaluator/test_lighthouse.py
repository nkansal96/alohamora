import io
import json
import re
import subprocess

from unittest import mock
import pytest

from blaze.evaluator.lighthouse import get_metrics, parse_pw_output
from tests.mocks.config import get_config, get_mahimahi_config

def is_valid_path(path):
  return re.fullmatch(r'^(/[^\x00\/]{1,255})*/?$', path) is not None

def basic_pw_output_json():
  return json.dumps({
    'runs': [{
      'timings': [
        {'id': 'speedIndex', 'timing': 1000}
      ]
    }]
  })

class TestParsePWOutput():
  def test_parse_pw_output_one_run(self):
    result = parse_pw_output({
      'runs': [{
        'timings': [
          {'id': 'speedIndex', 'timing': 1000}
        ]
      }]
    })
    assert result.speed_index == 1000

  def test_parse_pw_output_multiple_runs(self):
    result = parse_pw_output({
      'runs': [{
        'timings': [
          {'id': 'speedIndex', 'timing': 1000}
        ]
      }, {
        'timings': [
          {'id': 'speedIndex', 'timing': 1200}
        ]
      }]
    })
    assert result.speed_index == 1000

  def test_parse_pw_output_with_median(self):
    result = parse_pw_output({
      'median': {
        'timings': [
          {'id': 'speedIndex', 'timing': 1100}
        ]
      },
      'runs': [{
        'timings': [
          {'id': 'speedIndex', 'timing': 1000}
        ]
      }, {
        'timings': [
          {'id': 'speedIndex', 'timing': 1200}
        ]
      }]
    })
    assert result.speed_index == 1100

class TestGetMetrics():
  def setup(self):
    self.config = get_config()
    self.mahimahi_config = get_mahimahi_config()

  @mock.patch('tempfile.TemporaryDirectory')
  @mock.patch('builtins.open', new_callable=mock.mock_open, read_data=basic_pw_output_json())
  @mock.patch('subprocess.run')
  def test_get_metrics_reads_and_writes_files(self, mock_run, mock_open, mock_TemporaryDirectory):
    tmp_dir = '/tmp/blaze_test_123'
    mock_run.return_value = subprocess.CompletedProcess(
      args=[],
      returncode=0,
      stdout=io.StringIO(basic_pw_output_json())
    )
    mock_TemporaryDirectory.return_value.__enter__.return_value = tmp_dir

    metrics = get_metrics(self.config, self.mahimahi_config)
    print(mock_open.call_args_list[0][0][0])
    assert mock_open.call_args_list[0][0][0].startswith(tmp_dir)
    assert mock_open.call_args_list[1][0][0].startswith(tmp_dir)
    assert mock_open.call_args_list[2][0][0].startswith(tmp_dir)
    assert is_valid_path(mock_open.call_args_list[0][0][0])
    assert is_valid_path(mock_open.call_args_list[1][0][0])
    assert is_valid_path(mock_open.call_args_list[2][0][0])
    assert mock_open.call_args_list[0][0][1] == 'w'
    assert mock_open.call_args_list[1][0][1] == 'w'
    assert mock_open.call_args_list[2][0][1] == 'r'
    assert metrics.speed_index == 1000

  @mock.patch('tempfile.TemporaryDirectory')
  @mock.patch('builtins.open', new_callable=mock.mock_open, read_data=basic_pw_output_json())
  @mock.patch('subprocess.run')
  def test_get_metrics_spawns_subprocess_correctly(self, mock_run, mock_open, mock_TemporaryDirectory):
    mock_run.return_value = subprocess.CompletedProcess(
      args=[],
      returncode=0,
      stdout=io.StringIO(basic_pw_output_json())
    )
    mock_TemporaryDirectory.return_value.__enter__.return_value = '/tmp/blaze_test_123'
    metrics = get_metrics(self.config, self.mahimahi_config)
    mahimahi_cmd = self.mahimahi_config.proxy_replay_shell_with_cmd([])
    assert mock_run.called_once()
    assert mock_run.call_args_list[0].cmd.startswith(' '.join(mahimahi_cmd))
    assert metrics.speed_index == 1000

  @mock.patch('tempfile.TemporaryDirectory')
  @mock.patch('builtins.open', new_callable=mock.mock_open, read_data=basic_pw_output_json())
  @mock.patch('subprocess.run')
  def test_get_metrics_should_raise_if_subprocess_error(self, mock_run, mock_open, mock_TemporaryDirectory):
    mock_run.return_value = subprocess.CompletedProcess(
      args=[],
      returncode=1,
      stdout=io.StringIO(basic_pw_output_json())
    )
    mock_TemporaryDirectory.return_value.__enter__.return_value = '/tmp/blaze_test_123'
    with pytest.raises(subprocess.CalledProcessError):
      assert get_metrics(self.config, self.mahimahi_config).speed_index == 1000
