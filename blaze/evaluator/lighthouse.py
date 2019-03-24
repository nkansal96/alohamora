import collections
import contextlib
import itertools
import json
import os
import subprocess
import tempfile

from jinja2 import Template

from .chrome import get_chrome_flags
from .mahimahi import MahiMahiConfig
from .result import Results

PW_CMD_PATH = os.path.join(os.path.dirname(__file__), '../node_modules/.bin/pwmetrics')
TEMPLATE_FILE = os.path.join(os.path.dirname(__file__), 'templates/pwconfig.js.j2')
CONFIG_TEMPLATE = Template(open(TEMPLATE_FILE, 'r').read())

def parse_pw_output(output: dict):
  res = output.get("median", output["runs"][0])
  return Results({k["id"]: k["timing"] for k in res["timings"]})

def get_metrics(url, mahimahi_config: MahiMahiConfig):
  with tempfile.TemporaryDirectory(prefix='blaze_test', dir='/tmp') as tmp_dir:
    config_file = os.path.join(tmp_dir, 'pw_config.js')
    output_file = os.path.join(tmp_dir, 'pw_output.json')
    push_policy_file = os.path.join(tmp_dir, 'mm_push_policy')

    with open(config_file, 'w') as f:
      f.write(CONFIG_TEMPLATE.render(
        url=url,
        n_runs=1,
        output_path=output_file,
        chrome_flags=get_chrome_flags(tmp_dir),
        cpu_slowdown=mahimahi_config.environment.device_speed.value,
      ))

    mahimahi_cmd = mahimahi_config.cmd(push_policy_file)
    cmd = [*mahimahi_cmd, PW_CMD_PATH, '--config', config_file]
    # cwd='/' to write the output to the correct temporary folder. the folder
    # path is an absolute directory but there's a bug in pw-metrics that uses it
    # as a relative path despite the leading '/', so cwd to '/' to make it work
    proc = subprocess.run(' '.join(cmd),
      shell=True,
      cwd='/',
      stdout=subprocess.DEVNULL,
      stderr=subprocess.DEVNULL
    )
    proc.check_returncode()

    with open(output_file, 'r') as f:
      return parse_pw_output(json.load(f))
