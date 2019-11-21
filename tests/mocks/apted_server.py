import contextlib
import json
import threading
from urllib.parse import urlparse, parse_qs
from http.server import HTTPServer, SimpleHTTPRequestHandler


@contextlib.contextmanager
def apted_server(port, distances):
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

    server = HTTPServer(("", port), RequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    try:
        yield
    finally:
        server.shutdown()
        server_thread.join()
