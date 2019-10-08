""" This module defines a package-wide standard logger """
import os
import sys

import colorama

from .level import Level
from .logger import Logger

colorama.init()


def get_default_logger():
    """ Creates the default logger """

    def print_to_stderr(s: str):
        sys.stderr.write(s + "\n")

    min_level = Level.from_string(os.environ.get("LOG_LEVEL"))
    return Logger(namespace="blaze", min_level=min_level, print_fn=print_to_stderr)


logger = get_default_logger()  # pylint: disable=invalid-name  # disable for global access to logger
