import http.server
import os
import socketserver
import urllib.request

TUNNEL_URL = os.environ.get(
    "LAB28_TUNNEL_URL", "https://dishes-biggest-author-smaller.trycloudflare.com"
).rstrip("/")


class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        target_url = f"{TUNNEL_URL}{self.path}"
        try:
            req = urllib.request.Request(target_url, headers={"User-Agent": "vllm-proxy"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                content = resp.read()
                self.send_response(resp.status)
                for header, val in resp.getheaders():
                    if header.lower() not in ("transfer-encoding", "content-length", "connection"):
                        self.send_header(header, val)
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
        except Exception as e:
            self.send_response(502)
            self.end_headers()
            self.wfile.write(str(e).encode())

    def log_message(self, format: str, *args: object) -> None:
        pass


if __name__ == "__main__":
    port = 8001
    socketserver.TCPServer.allow_reuse_address = True
    server = socketserver.TCPServer(("0.0.0.0", port), ProxyHandler)
    print(f"Proxying port {port} -> {TUNNEL_URL}")
    server.serve_forever()
