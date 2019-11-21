import contextlib
import json
import threading
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, SimpleHTTPRequestHandler

from blaze.evaluator.cluster.distance import create_apted_distance_function
from tests.mocks.config import get_env_config

PORT = 25677


@contextlib.contextmanager
def apted_server(distances):
    class RequestHandler(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            self.i = 0
            super().__init__(*args, **kwargs)

        def do_GET(self):
            path = urlparse(self.path)
            q = parse_qs(path.query)
            assert path.path == "/getTreeDiff"
            assert "tree1" in q and "tree2" in q

            assert json.loads(q["tree1"][0])
            assert json.loads(q["tree2"][0])

            d = distances[self.i]
            self.i += 1

            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(bytes(f'{{"editDistance": {d}}}', encoding="utf-8"))

    server = HTTPServer(("", PORT), RequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    yield
    server.shutdown()
    server_thread.join()


class TestAptedDistance:
    def test(self):
        distances = [10]
        with apted_server(distances):
            distance_func = create_apted_distance_function(PORT)
            assert distance_func(get_env_config(), get_env_config()) == distances[0]
