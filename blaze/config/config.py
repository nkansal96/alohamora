""" This module defines the main Config used in launching training tasks """

import os
import platform
from typing import NamedTuple, Optional

from blaze.util.cmd import run
from .environment import EnvironmentConfig

ABSPATH = lambda path: os.path.abspath(os.path.join(os.path.dirname(__file__), path))

# pylint: disable=line-too-long
DEFAULT_MAHIMAHI_CERT_DIR = ABSPATH('../../mahimahi/src/frontend/certs')
DEFAULT_CHROME_HAR_CAPTURER_BIN = ABSPATH('../../third_party/node/node_modules/.bin/chrome-har-capturer')
DEFAULT_PWMETRICS_BIN = ABSPATH('../../third_party/node/node_modules/.bin/pwmetrics')
DEFAULT_NGHTTPX_BIN = run(['which', 'nghttpx'])
DEFAULT_CHROME_BIN = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome' if platform.system() == 'Darwin' else run(['which', 'google-chrome'])

class Config(NamedTuple):
  """ Config defines the parameters required to run blaze """
  mahimahi_cert_dir: str
  chrome_har_capturer_bin: str
  pwmetrics_bin: str
  nghttpx_bin: str
  chrome_bin: str
  train_config: Optional[EnvironmentConfig] = None

def get_config() -> Config:
  """
  get_config returns the runtime configuration, taking values from environment variables
  when available to override the defaults
  """
  return Config(
    mahimahi_cert_dir=os.environ.get('MAHIMAHI_CERT_DIR', DEFAULT_MAHIMAHI_CERT_DIR),
    chrome_har_capturer_bin=os.environ.get('CHROME_HAR_CAPTURER_BIN', DEFAULT_CHROME_HAR_CAPTURER_BIN),
    pwmetrics_bin=os.environ.get('PWMETRICS_BIN', DEFAULT_PWMETRICS_BIN),
    nghttpx_bin=os.environ.get('NGHTTPX_BIN', DEFAULT_NGHTTPX_BIN),
    chrome_bin=os.environ.get('CHROME_BIN', DEFAULT_CHROME_BIN),
  )
