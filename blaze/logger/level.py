""" This module defines the log levels and corresponding utilities """
import enum

from colorama import Fore, Style


@enum.unique
class Level(enum.IntEnum):
    """ Level defines the different log levels """

    DEBUG = 0
    INFO = 1
    WARN = 2
    ERROR = 3
    CRITICAL = 4

    def __str__(self):
        return ["debu", "info", "warn", "erro", "crit"][int(self.value)]

    @property
    def color(self):
        """ Returns the corresponding text color for each log level """
        return [Fore.LIGHTWHITE_EX, Fore.LIGHTBLUE_EX, Fore.YELLOW, Fore.LIGHTRED_EX, Fore.RED][int(self.value)]

    @property
    def context_key_color(self):
        """ Returns the corresponding context key text color for each log level """
        return [Style.DIM + Fore.LIGHTWHITE_EX, Fore.LIGHTBLUE_EX, Fore.YELLOW, Fore.LIGHTRED_EX, Fore.RED][
            int(self.value)
        ]
