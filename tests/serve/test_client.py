import grpc
import time

from blaze.action import ActionSpace
from blaze.config import client
from blaze.environment import Environment
from blaze.model.model import SavedModel
from blaze.serve.client import Client
from blaze.serve.server import Server
from blaze.serve.policy_service import PolicyService

from tests.mocks.agent import mock_agent_with_action_space
from tests.mocks.config import get_push_groups, get_serve_config


class TestClient:
    def setup(self):
        self.push_groups = get_push_groups()
        self.trainable_push_groups = [group for group in self.push_groups if group.trainable]
        self.serve_config = get_serve_config()
        self.action_space = ActionSpace(self.trainable_push_groups)
        self.mock_agent = mock_agent_with_action_space(self.action_space)
        self.saved_model = SavedModel(self.mock_agent, Environment, "/tmp/model_location")

    def test_get_policy(self):
        server = Server(self.serve_config)
        policy_service = PolicyService(self.saved_model)
        server.set_policy_service(policy_service)
        try:
            server.start()
            time.sleep(0.5)
            # create the client
            address = "{}:{}".format(self.serve_config.host, self.serve_config.port)
            channel = grpc.insecure_channel(address)
            client_stub = Client(channel)
            policy = client_stub.get_policy(
                url="https://www.example.com",
                network_type=client.NetworkType.LTE,
                device_speed=client.DeviceSpeed.FAST_MOBILE,
                resources=[res for group in self.push_groups for res in group.resources],
                train_domain_globs=[group.name for group in self.trainable_push_groups],
            )

            assert policy
            assert len(policy) > 0
            for k, v in policy.items():
                assert isinstance(v, list)
                assert all(isinstance(i, str) for i in v)
        finally:
            server.stop()
