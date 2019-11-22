import contextlib
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
import socketserver


@contextlib.contextmanager
def apted_server(port, distances):
    class RequestHandler(socketserver.BaseRequestHandler):
        def __init__(self, *args, **kwargs):
            self.i = 0
            super().__init__(*args, **kwargs)

        def handle(self):
            self.request.recv(65535)
            d = distances[self.i]
            self.i += 1

            rd = f'{{"editDistance": {d}}}'
            self.request.sendall(
                f"HTTP/1.1 200 OK\r\nContent-type: application/json\r\nContent-length: {len(rd)}\r\n\r\n{rd}".encode()
            )

    server = socketserver.TCPServer(("", port), RequestHandler)
    server_thread = threading.Thread(target=server.serve_forever)
    server_thread.start()
    try:
        yield
    finally:
        server.shutdown()
        server_thread.join()
