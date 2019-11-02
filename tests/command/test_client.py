import json
import pytest
import tempfile

from blaze.action import ActionSpace
from blaze.command.client import query
from blaze.config.environment import EnvironmentConfig
from blaze.environment import Environment
from blaze.model.model import SavedModel
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

    def test_client_exits_with_invalid_arguments(self):
        with pytest.raises(SystemExit):
            query([])
        with pytest.raises(SystemExit):
            query(["--manifest", "/tmp/manifest"])
        with pytest.raises(SystemExit):
            query(["--manifest", "/tmp/manifest", "-n", 0])
        with pytest.raises(SystemExit):
            query(["--manifest", "/tmp/manifest", "-d", 0])

    def test_client(self, capsys):
        server = Server(self.serve_config)
        server.set_policy_service(PolicyService(self.saved_model))

        try:
            server.start()

            with tempfile.NamedTemporaryFile() as manifest_file:
                config = EnvironmentConfig(
                    request_url="http://cs.ucla.edu/", replay_dir="/tmp/tmp_dir", push_groups=get_push_groups()
                )
                config.save_file(manifest_file.name)
                query(
                    [
                        "--manifest",
                        manifest_file.name,
                        "-n",
                        "1",
                        "-d",
                        "2",
                        "--host",
                        str(self.serve_config.host),
                        "--port",
                        str(self.serve_config.port),
                    ]
                )

            policy = json.loads(capsys.readouterr().out)
            assert policy
            assert len(policy) > 0
        finally:
            server.stop()
