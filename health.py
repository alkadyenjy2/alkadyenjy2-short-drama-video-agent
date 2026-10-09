# health.py - Minimal HTTP health endpoint for Railway + Docker
# GET /health returns 200 only when app + persistence initialized

import os
import json
import hmac
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading


def is_video_inventory_authorized(authorization: str, expected_token: str) -> bool:
    if not expected_token:
        return False
    return hmac.compare_digest(authorization or "", f"Bearer {expected_token}")

class HealthHandler(BaseHTTPRequestHandler):
    def __init__(self, repository_getter, *args, **kwargs):
        self.repository_getter = repository_getter
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        if self.path == "/health":
            try:
                repo = self.repository_getter()
                healthy = repo.health_check() if repo else False
                if healthy:
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "status": "ok",
                        "service": "video-agent",
                        "persistence": "ok",
                        "version": "v1.2"
                    }
                    self.wfile.write(json.dumps(response).encode())
                else:
                    self.send_response(503)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "status": "error",
                        "service": "video-agent",
                        "persistence": "failed",
                        "version": "v1.2"
                    }
                    self.wfile.write(json.dumps(response).encode())
            except Exception as e:
                self.send_response(503)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {
                    "status": "error",
                    "service": "video-agent",
                    "persistence": "exception",
                    "version": "v1.2"
                }
                self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        # Suppress default logging
        return

def start_health_server(repository_getter, host="0.0.0.0", port=8000):
    # Factory to inject repository_getter
    def handler(*args, **kwargs):
        HealthHandler(repository_getter, *args, **kwargs)
    
    # Use closure to pass getter
    class CustomHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            if self.path == "/health":
                try:
                    repo = repository_getter()
                    healthy = repo.health_check() if repo else False
                    if healthy:
                        self.send_response(200)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        response = {
                            "status": "ok",
                            "service": "video-agent",
                            "persistence": "ok",
                            "version": "v1.2"
                        }
                        self.wfile.write(json.dumps(response).encode())
                    else:
                        self.send_response(503)
                        self.send_header("Content-type", "application/json")
                        self.end_headers()
                        response = {
                            "status": "error",
                            "service": "video-agent",
                            "persistence": "failed",
                            "version": "v1.2"
                        }
                        self.wfile.write(json.dumps(response).encode())
                except Exception as e:
                    self.send_response(503)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    response = {
                        "status": "error",
                        "service": "video-agent",
                        "persistence": "exception",
                        "version": "v1.2",
                        "error": "hidden"  # Do not expose internal stack traces
                    }
                    self.wfile.write(json.dumps(response).encode())
            elif self.path == "/release-assets":
                # Public, read-only inventory of real files attached to the
                # verified GitHub release. This is not proof of social-platform publication.
                manifest_path = os.path.join(os.path.dirname(__file__), "evidence", "the-envelope-release-assets.json")
                try:
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        manifest = json.load(f)
                    assets = manifest.get("assets") if isinstance(manifest, dict) else None
                    if not isinstance(assets, list):
                        raise ValueError("invalid release asset manifest")
                    response = {
                        "count": len(assets),
                        "assets": assets,
                        "release_url": manifest.get("release_url"),
                        "publication_status": "release_asset_only",
                        "platform_published": False,
                    }
                    body = json.dumps(response).encode()
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except (OSError, ValueError):
                    self.send_response(503)
                    self.send_header("Content-type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "release asset catalog unavailable"}).encode())
            elif self.path == "/videos":
                expected_token = os.getenv("VIDEO_API_TOKEN", "").strip()
                authorization = self.headers.get("Authorization", "")
                if not is_video_inventory_authorized(authorization, expected_token):
                    self.send_response(401)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "unauthorized"}).encode())
                    return
                try:
                    repo = repository_getter()
                    videos = repo.list_video_versions() if repo else None
                    if videos is None:
                        raise RuntimeError("repository unavailable")
                    self.send_response(200)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(json.dumps({"videos": videos, "storage": "persistent"}).encode())
                except Exception:
                    self.send_response(503)
                    self.send_header("Content-type", "application/json")
                    self.send_header("Cache-Control", "no-store")
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "video inventory unavailable"}).encode())
            else:
                self.send_response(404)
                self.end_headers()
        
        def log_message(self, format, *args):
            return
    
    server = HTTPServer((host, port), CustomHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, thread
