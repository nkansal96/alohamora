import pytest
from unittest import mock

from blaze.command import command


class TestCommand:
    def test_init(self):
        cmd = command.Command("name", " desc   ", lambda x: x)
        assert isinstance(cmd, command.Command)
        assert cmd.name == "name"
        assert cmd.desc == "desc"  # also tests that the desc is stripped of whitespace
        assert cmd.func(1) == 1

    def test_description(self):
        cmd = command.Command("name", "orig_desc", lambda x: x)
        assert cmd.desc == "orig_desc"
        cmd.description("desc")
        assert cmd.desc == "desc"

    def test_argument(self):
        cmd = command.Command("name", "desc", lambda x: x)
        cmd.argument(1, "a", ["test"], keyword="test")
        assert len(cmd.args) == 1
        assert cmd.args[0] == ((1, "a", ["test"]), {"keyword": "test"})

        cmd.argument(2, "b", ["test"], another_arg="test2")
        assert len(cmd.args) == 2
        assert cmd.args[0] == ((1, "a", ["test"]), {"keyword": "test"})
        assert cmd.args[1] == ((2, "b", ["test"]), {"another_arg": "test2"})

    def test_call_success(self):
        def fn(args):
            fn.called = True
            assert args.test == 123
            assert args.f == 100

        fn.called = False
        cmd = command.Command("fn", "desc", fn)
        cmd.argument("test", type=int)
        cmd.argument("-f", required=True, type=int)
        cmd(["123", "-f", "100"])
        assert fn.called

    def test_call_failure(self):
        def fn(args):
            fn.called = True
            assert args.test == 123
            assert args.f == 100

        fn.called = False
        cmd = command.Command("fn", "desc", fn)
        cmd.argument("test", type=int)
        cmd.argument("-f", required=True, type=int)
        with pytest.raises(SystemExit):
            cmd(["123"])
        assert not fn.called


class TestCommandDecorator:
    def test_command_creates_command(self):
        try:
            assert "test_fn" not in command.COMMANDS

            @command.command
            def test_fn(args):
                """ test_fn_desc """
                return 1

            assert isinstance(test_fn, command.Command)
            assert test_fn.name == "test_fn"
            assert test_fn.desc == "test_fn_desc"
            assert test_fn.func(None) == 1
            assert "test_fn" in command.COMMANDS
        finally:
            command.COMMANDS.pop("test_fn", None)


class TestDescriptionDecorator:
    def test_description_fails_if_used_on_non_command(self):
        with pytest.raises(TypeError):

            @command.description("test")
            def test_fn(args):
                pass

    def test_description_adds_description_to_command(self):
        try:

            @command.description("test")
            @command.command
            def test_fn(args):
                """ orig_desc """
                pass

            assert test_fn.desc == "test"
        finally:
            command.COMMANDS.pop("test_fn", None)


class TestArgumentDecorator:
    def test_argument_fails_if_used_on_non_command(self):
        with pytest.raises(TypeError):

            @command.argument("test")
            def test_fn(args):
                pass

    def test_argument_adds_argument_to_command(self):
        try:

            @command.description("test")
            @command.argument("--test_a", required=True)
            @command.argument("--test_b", default="test")
            @command.command
            def test_fn(args):
                pass

            assert test_fn.desc == "test"
            assert test_fn.args == [(("--test_b",), {"default": "test"}), (("--test_a",), {"required": True})]
        finally:
            command.COMMANDS.pop("test_fn", None)


class TestHelpText:
    def test_help_text(self):
        text = command.help_text()
        for cmd in command.COMMANDS:
            assert cmd in text


class TestRun:
    @mock.patch("builtins.print")
    def test_run_nonexistent_command(self, mock_print):
        with pytest.raises(SystemExit):
            command.run("non_existent", [])
        mock_print.assert_called_once()
        mock_print.assert_called_with(command.help_text())

    def test_run_command(self):
        try:

            @command.argument("test")
            @command.command
            def test_fn(args):
                return args.test

            assert command.run("test_fn", ["100"]) == "100"
        finally:
            command.COMMANDS.pop("test_fn", None)
