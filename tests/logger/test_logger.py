import re
import sys
from unittest import mock

from blaze.logger import Level, Logger


def strip_ansi(text):
    ansi_escape = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
    return ansi_escape.sub("", text)


class MockPrint:
    def __init__(self):
        self.called_with = None

    def __call__(self, called_with):
        self.called_with = strip_ansi(called_with)

    @property
    def called(self):
        return self.called_with


def create_logger(*args, **kwargs):
    print_fn = MockPrint()
    return print_fn, Logger(*args, **kwargs, print_fn=print_fn)


class TestLogger:
    def test_init(self):
        log = Logger(
            namespace="test", min_level=Level.INFO, time_start=0, print_fn=sys.stderr.write, context={"test": 100}
        )
        assert isinstance(log, Logger)
        assert log.namespace == "test"
        assert log.min_level == Level.INFO
        assert log.time_start == 0
        assert log.print_fn == sys.stderr.write
        assert len(log.context) == 1
        assert log.context["test"] == 100

    def test_log_without_level_does_nothing(self):
        print_fn, log = create_logger(min_level=Level.DEBUG)
        log.log()
        assert not print_fn.called

    def test_log_with_level_lower_than_min_level_does_nothing(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        log.log(level=Level.DEBUG)
        assert not print_fn.called

    def test_log_with_level(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        log.log(level=Level.INFO)
        assert print_fn.called_with == "[{}]".format(str(Level.INFO))

    def test_log_with_name(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        namespace = "blaze"
        log.log(level=Level.INFO, namespace=namespace)
        assert print_fn.called_with == "[{}] {}:".format(str(Level.INFO), namespace)

    def test_log_with_message(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        message = "this is a message"
        log.log(level=Level.INFO, message=message)
        assert print_fn.called_with == "[{}] {}".format(str(Level.INFO), message)

    def test_log_with_name_and_message(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        namespace = "blaze"
        message = "this is a message"
        log.log(level=Level.INFO, namespace=namespace, message=message)
        assert print_fn.called_with == "[{}] {}: {}".format(str(Level.INFO), namespace, message)

    def test_log_with_context(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        context = {"test": 123, "another": "test"}
        log.log(level=Level.INFO, **context)
        assert print_fn.called_with == "[{}] {}".format(
            str(Level.INFO), " ".join("{}={}".format(*c) for c in context.items())
        )

    def test_log_with_name_and_context(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        namespace = "blaze"
        context = {"test": 123, "another": "test"}
        log.log(level=Level.INFO, namespace=namespace, **context)
        assert print_fn.called_with == "[{}] {}: {}".format(
            str(Level.INFO), namespace, " ".join("{}={}".format(*c) for c in context.items())
        )

    def test_log_with_name_message_and_context(self):
        print_fn, log = create_logger(min_level=Level.INFO)
        namespace = "blaze"
        message = "this is a message"
        context = {"test": 123, "another": "test"}
        log.log(level=Level.INFO, namespace=namespace, message=message, **context)
        assert print_fn.called_with == "[{}] {}: {} {}".format(
            str(Level.INFO), namespace, message, " ".join("{}={}".format(*c) for c in context.items())
        )

    def test_debug(self):
        print_fn, log = create_logger(min_level=Level.DEBUG)
        log.debug("")
        assert print_fn.called_with.startswith("[{}]".format(str(Level.DEBUG)))

    def test_info(self):
        print_fn, log = create_logger(min_level=Level.DEBUG)
        log.info("")
        assert print_fn.called_with.startswith("[{}]".format(str(Level.INFO)))

    def test_warn(self):
        print_fn, log = create_logger(min_level=Level.DEBUG)
        log.warn("")
        assert print_fn.called_with.startswith("[{}]".format(str(Level.WARN)))

    def test_error(self):
        print_fn, log = create_logger(min_level=Level.DEBUG)
        log.error("")
        assert print_fn.called_with.startswith("[{}]".format(str(Level.ERROR)))

    def test_critical(self):
        print_fn, log = create_logger(min_level=Level.DEBUG)
        log.critical("")
        assert print_fn.called_with.startswith("[{}]".format(str(Level.CRITICAL)))
