import grpc
from unittest import mock

from blaze.action import ActionSpace
from blaze.environment import Environment
from blaze.model.model import SavedModel
from blaze.proto import policy_service_pb2
from blaze.proto import policy_service_pb2_grpc
from blaze.serve.server import Server
from blaze.serve.policy_service import PolicyService

from tests.mocks.agent import mock_agent_with_action_space
from tests.mocks.config import get_push_groups, get_serve_config, convert_push_groups_to_push_pairs
from tests.mocks.serve import get_page


class TestServer:
    def setup(self):
        self.push_groups = get_push_groups()
        self.trainable_push_groups = [group for group in self.push_groups if group.trainable]
        self.serve_config = get_serve_config()
        self.action_space = ActionSpace(self.trainable_push_groups)
        self.mock_agent = mock_agent_with_action_space(self.action_space)
        self.saved_model = SavedModel(self.mock_agent, Environment, "/tmp/model_location")

    def test_init(self):
        server = Server(self.serve_config)
        assert server
        assert isinstance(server, Server)
        assert server.config is self.serve_config
        assert not server.server_started

    @mock.patch("blaze.serve.server.grpc._server._Server")
    def test_set_policy_service(self, mock_grpc_server):
        server = Server(self.serve_config)
        server.set_policy_service(PolicyService(self.saved_model))
        print(server.grpc_server)
        server.grpc_server.add_generic_rpc_handlers.assert_called_once()

    @mock.patch("blaze.serve.server.grpc._server._Server")
    def test_start_server(self, mock_grpc_server):
        server = Server(self.serve_config)
        server.set_policy_service(PolicyService(self.saved_model))
        server.start()

        server.grpc_server.start.assert_called_once()
        server.grpc_server.add_insecure_port.assert_called_once()
        assert ":{}".format(self.serve_config.port) in server.grpc_server.add_insecure_port.call_args_list[0][0][0]
        assert server.server_started

    def test_server_serves_policy(self):
        # configure the server
        server = Server(self.serve_config)
        policy_service = PolicyService(self.saved_model)
        server.set_policy_service(policy_service)
        try:
            # start the server
            server.start()
            # create the client
            address = "{}:{}".format(self.serve_config.host, self.serve_config.port)
            channel = grpc.insecure_channel(address)
            stub = policy_service_pb2_grpc.PolicyServiceStub(channel)
            # query for the policy for some page
            page = get_page("https://example.com")
            policy = stub.GetPolicy(page)
            # check whether we got a reasonable return value
            # we'll check for correctness in the policy_service unit tests
            assert policy
            assert isinstance(policy, policy_service_pb2.Policy)
        finally:
            server.stop()
