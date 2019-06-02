from blaze.command.analyze import analyze
from types import SimpleNamespace


class TestAnalyze:
    def test_analyze(self):
        analyze(["/tmp/eval_results_dir"])
        assert True
