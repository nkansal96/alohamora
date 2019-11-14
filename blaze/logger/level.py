""" This module defines the log levels and corresponding utilities """
import enum

from colorama import Fore, Style


@enum.unique
class Level(enum.IntEnum):
    """ Level defines the different log levels """

    VERBOSE = 0
    DEBUG = 1
    INFO = 2
    WARN = 3
    ERROR = 4
    CRITICAL = 5

    def __str__(self):
        return ["verb", "debu", "info", "warn", "erro", "crit"][int(self.value)]

    @property
    def color(self):
        """ Returns the corresponding text color for each log level """
        return [Fore.WHITE, Fore.LIGHTWHITE_EX, Fore.LIGHTBLUE_EX, Fore.YELLOW, Fore.LIGHTRED_EX, Fore.RED][
            int(self.value)
        ]

    @property
    def context_key_color(self):
        """ Returns the corresponding context key text color for each log level """
        return [
            Style.DIM + Fore.WHITE,
            Style.DIM + Fore.LIGHTWHITE_EX,
            Fore.LIGHTBLUE_EX,
            Fore.YELLOW,
            Fore.LIGHTRED_EX,
            Fore.RED,
        ][int(self.value)]

    @staticmethod
    def from_string(level_str: str):
        """
        Returns the log Level from the given level string
        """
        if not level_str:
            return Level.INFO
        valid_level_strings = ["verb", "debu", "info", "warn", "erro", "crit"]
        for i, level in enumerate(valid_level_strings):
            if level_str.lower().startswith(level):
                return Level(i)
        return Level.INFO
