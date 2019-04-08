""" This module defines a package-wide standard logger """
import os

import colorama

from .level import Level
from .logger import Logger

colorama.init()

def get_default_logger():
  """ Creates the default logger """
  min_level = Level.DEBUG if 'DEBUG' in os.environ else Level.INFO
  return Logger(namespace='blaze', min_level=min_level)

logger = get_default_logger() # pylint: disable=invalid-name  # disable for global access to logger
