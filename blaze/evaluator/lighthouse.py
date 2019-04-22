""" This module defines methods to interact with Lighthouse """
import json
import os
import subprocess
import tempfile

from blaze.config import Config
from blaze.chrome.config import get_chrome_flags
from blaze.logger import logger
from blaze.mahimahi import MahiMahiConfig

from .result import Result

CONFIG_TEMPLATE = '''module.exports = {{
  url: '{url}',
  flags: {{
    runs: {runs},
    json: true,
    outputPath: '{output_path}',
    chromePath: '{chrome_path}',
    chromeFlags: '{chrome_flags}',
    showOutput: false,
    disableCpuThrottling: false,
    throttling: {{
      cpuSlowdownMultiplier: {cpu_slowdown},
    }},
  }},
}}
'''

def parse_pw_output(output: dict) -> Result:
  """
  Parses the output of the pwmetrics application and returns a Result object
  containing the measured metrics
  """
  res = output.get('median', output['runs'][0])
  return Result(**{k['id']: k['timing'] for k in res['timings']})

def get_metrics(config: Config, mahimahi_config: MahiMahiConfig) -> Result:
  """
  Sets up and executes the Mahimahi environment and pwmetrics application (wrapper
  around Lighthouse) to load a webpage and returns the recorded metrics
  """
  log = logger.with_namespace('lighthouse')
  with tempfile.TemporaryDirectory(prefix='blaze_test', dir='/tmp') as tmp_dir:
    config_file = os.path.join(tmp_dir, 'pw_config.js')
    output_file = os.path.join(tmp_dir, 'pw_output.json')
    push_policy_file = os.path.join(tmp_dir, 'mm_push_policy')
    trace_file = os.path.join(tmp_dir, 'trace')

    with open(config_file, 'w') as f:
      f.write(CONFIG_TEMPLATE.format(
        url=config.env_config.request_url,
        runs=1,
        output_path=output_file,
        chrome_path=config.chrome_bin,
        chrome_flags=' '.join(get_chrome_flags(tmp_dir)),
        cpu_slowdown=mahimahi_config.client_environment.cpu_slowdown,
      ))
      log.debug('wrote lighthouse config', file=config_file)

    with open(push_policy_file, 'w') as f:
      f.write(mahimahi_config.formatted_push_policy)
      log.debug('wrote mahimahi push config', file=push_policy_file)

    with open(trace_file, 'w') as f:
      f.write(mahimahi_config.formatted_trace_file)
      log.debug('wrote formatted trace file', file=trace_file)

    cmd = mahimahi_config.proxy_replay_shell_with_cmd(push_policy_file, trace_file, [config.pwmetrics_bin, '--config', config_file])
    # cwd='/' to write the output to the correct temporary folder. the folder
    # path is an absolute directory but there's a bug in pwmetrics that uses it
    # as a relative path despite the leading '/', so cwd to '/' to make it work
    log.debug('starting lighthouse...')
    proc = subprocess.run(
      ' '.join(cmd),
      shell=True,
      cwd='/',
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL
    )
    proc.check_returncode()

    with open(output_file, 'r') as f:
      log.debug('received results', file=output_file)
      return parse_pw_output(json.load(f))
