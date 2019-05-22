from blaze.util.cmd import run


class TestRun:
    def test_run_success(self):
        cmd = ["which", "which"]
        res = run(cmd)
        assert "which" in res

    def test_run_failure(self):
        cmd = ["which", "a_command_that_definitely_does_not_exist"]
        res = run(cmd)
        assert res == ""
