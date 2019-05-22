""" This module defines simple utilities to run subprocess commands """
import subprocess
from typing import List


def run(cmd: List[str]) -> str:
    """
    run_cmd runs the specified command and returns what was printed to stdout. If the
    process exits with return code != 0, it returns an empty string
    """
    try:
        proc = subprocess.run(cmd, stdout=subprocess.PIPE)
        proc.check_returncode()
        return proc.stdout.decode("utf-8").strip()
    except subprocess.CalledProcessError:
        return ""
