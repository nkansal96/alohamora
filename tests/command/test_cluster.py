import json
import pytest
import tempfile

from blaze.command.cluster import cluster

from tests.mocks.apted_server import apted_server
from tests.mocks.config import get_env_config


class TestClient:
    def test_client_exits_with_invalid_arguments(self):
        with pytest.raises(SystemExit):
            cluster([])

    def test_cluster(self, capsys):
        port = 24451
        distances = [0] * 100
        env_config = get_env_config()
        with tempfile.TemporaryDirectory() as tmp_dir:
            for i in range(3):
                env_config._replace(request_url=env_config.request_url + str(i)).save_file(f"{tmp_dir}/{i}.manifest")

            with apted_server(port, distances):
                cluster(["--apted_port", str(port), tmp_dir])

            resp = json.loads(capsys.readouterr().out)
            assert resp
            assert len(resp) > 0
            for url, mapping in resp.items():
                assert mapping == 0
