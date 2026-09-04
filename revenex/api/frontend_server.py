from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os


ROOT = (
    Path(__file__).resolve().parents[2]
    / "frontend"
)


class FrontendHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            directory=str(ROOT),
            **kwargs,
        )

    def log_message(self, format, *args):
        return


def serve(
    host="127.0.0.1",
    port=8788,
):
    server = ThreadingHTTPServer(
        (host, port),
        FrontendHandler,
    )

    print(
        f"REVENEX frontend: "
        f"http://{host}:{port}/revenue_command_center.html"
    )

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    serve()
