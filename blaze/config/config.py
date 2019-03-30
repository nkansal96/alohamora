""" This module defines the main Config used in launching training tasks """

from typing import NamedTuple, Optional
from .train import TrainConfig

class Config(NamedTuple):
  """ Config defines the parameters of launching a training task """
  mahimahi_cert_dir: str
  chrome_har_capturer_bin: str
  pwmetrics_bin: str
  nghttpx_bin: str
  chrome_bin: str
  train_config: Optional[TrainConfig] = None
