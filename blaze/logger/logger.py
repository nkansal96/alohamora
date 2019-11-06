""" This module defines the main logger """
import time

from colorama import Style

from .level import Level


class Logger:
    """ Logger is a class that logs some messages to a defined output stream """

    def __init__(self, namespace=None, min_level=Level.INFO, time_start=time.time(), print_fn=print, context=None):
        self.namespace = namespace
        self.min_level = min_level
        self.time_start = time_start
        self.print_fn = print_fn
        self.context = context or {}
        self.silent = False

    def log(self, level=None, namespace=None, message="", **context):
        """ Logs a message with the given level, namespace, message, and contextual information """
        if level is None or level < self.min_level or self.silent:
            return

        level_str = "[" + level.color + str(level) + Style.RESET_ALL + "]"
        namespace_str = (
            (Style.BRIGHT + " {}:".format(namespace or self.namespace) + Style.RESET_ALL)
            if namespace or self.namespace
            else ""
        )

        ctx = {**self.context, **context}
        ctx_fmt = level.context_key_color + "{}" + Style.RESET_ALL + "={}"
        ctx_str = " ".join(ctx_fmt.format(*c) for c in ctx.items())
        if message:
            message = " " + message
        if ctx:
            ctx_str = " " + ctx_str
        self.print_fn("{}{}{}{}".format(level_str, namespace_str, message, ctx_str))

    def with_namespace(self, namespace):
        """ Creates a new Logger inheriting the properties of this logger with a new namespace """
        return Logger(
            namespace=namespace,
            min_level=self.min_level,
            time_start=self.time_start,
            print_fn=self.print_fn,
            context=self.context,
        )

    def with_context(self, **context):
        """ Creates a new Logger inheriting the properties of this logger with some addional/overriden context """
        return Logger(
            namespace=self.namespace,
            min_level=self.min_level,
            time_start=self.time_start,
            print_fn=self.print_fn,
            context={**self.context, **context},
        )

    def debug(self, message, **context):
        """ Logs the given message with the debug level """
        self.log(level=Level.DEBUG, message=message, **context)

    def info(self, message, **context):
        """ Logs the given message with the info level """
        self.log(level=Level.INFO, message=message, **context)

    def warn(self, message, **context):
        """ Logs the given message with the warn level """
        self.log(level=Level.WARN, message=message, **context)

    def error(self, message, **context):
        """ Logs the given message with the error level """
        self.log(level=Level.ERROR, message=message, **context)

    def critical(self, message, **context):
        """ Logs the given message with the critical level """
        self.log(level=Level.CRITICAL, message=message, **context)

    def set_silence(self, silence: bool):
        """ Temporarily enable/disable logging """
        self.silent = silence
