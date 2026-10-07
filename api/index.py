import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from web_app import app

# Vercel rewrites public paths to this function while preserving the request path.
for route in list(app.routes):
    path = getattr(route, "path", "")
    if path and not path.startswith("/api/") and path != "/api" and path != "/":
        methods = getattr(route, "methods", None)
        if methods:
            app.add_api_route(f"/api{path}", route.endpoint, methods=list(methods), include_in_schema=False)
