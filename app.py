"""Start the local Smart Travel Agent web app."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import traceback
from urllib.parse import urlparse

from travel_planner import make_plan


ROOT = Path(__file__).parent


class Handler(BaseHTTPRequestHandler):
    def _send(self, status: int, content: bytes, content_type: str = "text/html; charset=utf-8") -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def do_GET(self) -> None:
        if urlparse(self.path).path not in {"/", "/index.html"}:
            self._send(404, b"Not found", "text/plain; charset=utf-8")
            return
        self._send(200, (ROOT / "index.html").read_bytes())

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/plan":
            self._send(404, b'{"error":"Not found"}', "application/json; charset=utf-8")
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size > 20_000:
                raise ValueError("Request is too large.")
            data = json.loads(self.rfile.read(size))
            if not isinstance(data, dict):
                raise ValueError("Please submit trip details as a form.")
            result = make_plan(data)
            payload = json.dumps(result, ensure_ascii=False).encode("utf-8")
            self._send(200, payload, "application/json; charset=utf-8")
        except (ValueError, json.JSONDecodeError) as exc:
            payload = json.dumps({"error": str(exc)}).encode()
            self._send(400, payload, "application/json; charset=utf-8")
        except Exception:
            traceback.print_exc()
            payload = json.dumps({"error": "The planner hit an unexpected error. Check the Python terminal for details."}).encode()
            self._send(500, payload, "application/json; charset=utf-8")

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"{self.address_string()} - {fmt % args}")


if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("Smart Travel Agent is ready at http://127.0.0.1:8000 (Ctrl+C to stop)")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nTravel Agent stopped.")
    finally:
        server.server_close()
