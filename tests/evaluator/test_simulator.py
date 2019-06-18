import json

from blaze.action import ActionSpace, Policy
from blaze.chrome.har import har_from_json
from blaze.config.client import get_fast_mobile_client_environment
from blaze.config.environment import EnvironmentConfig
from blaze.evaluator.simulator import Node, QueueItem, RequestQueue, Simulator
from blaze.preprocess.har import har_entries_to_resources
from blaze.preprocess.resource import resource_list_to_push_groups

from tests.mocks.config import get_env_config
from tests.mocks.har import get_har_json


# class TestRequestQueue:
#     def test_request_queue(self):
#         node_7 = Node(url="7", size=1000000, order=7, delay_ms=0, children=[])
#         node_5 = Node(url="5", size=200000, order=5, delay_ms=0, children=[])
#         node_3 = Node(url="3", size=40000, order=3, delay_ms=0, children=[])
#         node_4 = Node(url="4", size=90000, order=4, delay_ms=1000, children=[])
#         node_6 = Node(url="6", size=5000, order=6, delay_ms=2000, children=[])
#         node_2 = Node(url="2", size=100000, order=2, delay_ms=0, children=[node_4, node_6])
#         root = Node(url="1", size=10000, order=1, delay_ms=0, children=[node_2, node_3, node_5, node_7])
#
#         rq = RequestQueue(10000)
#         rq.add(node_2)
#         rq.add(node_3)
#         rq.add(node_5)
#         rq.add(node_7)
#
#         count = 0
#         while rq:
#             # print(rq.queue)
#             count += 1
#             completed, time_ms = rq.step()
#             # print([node.order for node in completed], time_ms, bytes_processed)
#             # print(rq.step())
#         assert count == 4

class TestSimulator:
    def test_simulator(self):
        # with open("/tmp/har.json", "r") as f:
        #     har = har_from_json(f.read())
        #     print(har.page_load_time_ms)
        har_json = get_har_json()
        har = har_from_json(har_json)
        res_list = har_entries_to_resources(har)
        push_groups = resource_list_to_push_groups(res_list)
        env_config = EnvironmentConfig(
            replay_dir="",
            request_url="https://www.reddit.com/",
            push_groups=push_groups,
            har_resources=res_list,
        )

        # env_config = get_env_config()
        client_env = get_fast_mobile_client_environment()

        simulator = Simulator(env_config)
        simulator.print_execution_map()
        time_ms = simulator.simulate_load_time(client_env)
        print(time_ms)
