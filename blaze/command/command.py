"""
Command implements a lightweight decorator-based interface to defining many
command-line sub-commands
"""
import argparse
import re
import sys
from types import SimpleNamespace
from typing import Any, Callable, List

COMMANDS = {}


class Command:
    """
    Command represents a single command, wrapping the command name, function, description,
    arguments, and argument parsing into one
    """

    def __init__(self, name: str, desc: str, func: Callable[[SimpleNamespace], Any]):
        self.name = name
        self.func = func
        self.desc = (desc or "").strip()
        self.args = []

    def __call__(self, argv: List[str]):
        """
        Calls the underlying command function with the equivalent of sys.argv (omitting the
        command name). It first parses the list of arguments with argparse, returning an error
        with help information if not valid. Then it calls the wrapped function with the parsed
        arguments and returns its return value.
        """
        parser = argparse.ArgumentParser(prog="blaze " + self.name, description=self.desc)
        for (args, kwargs) in self.args:
            parser.add_argument(*args, **kwargs)
        parsed_args = parser.parse_args(argv)
        return self.func(parsed_args)

    def description(self, desc: str):
        """ Sets the description for this command """
        self.desc = desc.strip()

    def argument(self, *args, **kwargs):
        """
        Adds an argument for this command. See the argparse add_argument method to see the
        valid configuration arguments for this method
        """
        self.args.append((args, kwargs))


def command(func: Callable[[SimpleNamespace], Any]):
    """
    Creates a command from the given function and adds it to the global list of
    commands. The wrapped function must take a single argument (the parsed arguments
    from argparse). This method returns an instance of a Command class.
    """
    cmd = Command(func.__name__, func.__doc__, func)
    COMMANDS[func.__name__] = cmd
    return cmd


def description(desc: str):
    """ Decorator that adds a description to a Command """

    def decorator(cmd: Command):
        if not isinstance(cmd, Command):
            raise TypeError("command.description() can only be applied after command.command()")
        cmd.description(desc)
        return cmd

    return decorator


def argument(*args, **kwargs):
    """ Decorator that adds an argument to a Command """

    def decorator(cmd: Command):
        if not isinstance(cmd, Command):
            raise TypeError("command.argument() can only be applied after command.command()")
        cmd.argument(*args, **kwargs)
        return cmd

    return decorator


def help_text():
    """ Returns the help text for all of the registered commands """
    header = """Blaze is an automated framework to analyze websites and generate push policies using
reinforcement learning. The basic usage of this tool is:
  $ blaze [command] [command-specific-arguments]
  
The following commands are available:

"""

    footer = "\nTo see the usage for a particular command, run blaze [command] -h"

    max_command_len = max(map(len, COMMANDS.keys()))
    max_line_length = 80

    def format_command(name, desc):
        name_str = "  {name: >{max_len}}: ".format(name=name, max_len=max_command_len)
        desc_width = max_line_length - len(name_str)
        lines = [[]]
        for word in re.split(r"\s+", desc):
            if sum(map(len, lines[-1])) + len(lines[-1]) + len(word) < desc_width:
                lines[-1].append(word)
            else:
                lines.append([word])
        desc_str = ("\n" + (" " * (len(name_str)))).join(" ".join(line) for line in lines)
        return name_str + desc_str

    command_info = format_command("help", "Display this help text") + "\n"
    command_info += "\n".join(format_command(c.name, c.desc) for c in COMMANDS.values())
    return header + command_info + footer


def run(fn_name, argv):
    """
    Runs a command by name with the given arguments. Note that the command name
    should be taken out of the passed argument list, which will be parsed without any
    information about commands
    """
    if not fn_name or fn_name == "" or fn_name not in COMMANDS:
        print(help_text())
        sys.exit(1)
    return COMMANDS[fn_name](argv)
