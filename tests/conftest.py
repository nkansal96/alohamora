""" Defines pytest fixtures to be used for testing """
import os
import pytest


@pytest.fixture(scope="session")
def is_ci():
    """ Returns true if the current environment is CI """
    return "CI" in os.environ
