from blaze.evaluator.cluster.distance import create_apted_distance_function
from tests.mocks.config import get_env_config
from tests.mocks.apted_server import apted_server

PORT = 25677


class TestAptedDistance:
    def test(self):
        distances = [10]
        with apted_server(PORT, distances):
            distance_func = create_apted_distance_function(PORT)
            assert distance_func(get_env_config(), get_env_config()) == distances[0]
