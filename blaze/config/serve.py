""" This module defines the configuration for a policy server """
from typing import NamedTuple

class ServeConfig(NamedTuple):
  """ The main configuration for the policy server """
  host: str
  port: int
  max_workers: int
