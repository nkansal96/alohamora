import json

from blaze.chrome.har import har_from_json
from blaze.config.client import get_fast_mobile_client_environment
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator.simulator import Simulator
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.resource import resource_list_to_push_groups

from tests.mocks.har import get_har_json


class TestSimulator:
    def test_simulator(self):
        har_json = get_har_json()
        har = har_from_json(har_json)
        res_list = har_entries_to_resources(har)
        push_groups = resource_list_to_push_groups(res_list)
        env_config = EnvironmentConfig(
            replay_dir="", request_url="https://www.reddit.com/", push_groups=push_groups, har_resources=res_list
        )

        client_env = get_fast_mobile_client_environment()

        simulator = Simulator(env_config)
        time_ms = simulator.simulate_load_time(client_env)
        assert time_ms > 0
