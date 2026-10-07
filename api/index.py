import os, sys
from fastapi import Request
from fastapi.responses import HTMLResponse, JSONResponse

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from web_app import app

@app.middleware("http")
async def normalize_vercel_path(request, call_next):
    path = request.scope.get("path", "")
    for prefix in ("/api/index.py", "/api/index", "/api"):
        if path == prefix:
            request.scope["path"] = "/"
            break
        if path.startswith(prefix + "/"):
            request.scope["path"] = path[len(prefix):] or "/"
            break
    return await call_next(request)
from web_app import health as _health
from web_app import get_stories as _stories
from web_app import agent_status as _agent_status
from web_app import publisher_status as _publisher_status

DASHBOARD = """<!doctype html><html lang='ar' dir='rtl'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>DRAMA AI — Short Drama Video Agent</title><style>body{font-family:system-ui;background:#0a0a0f;color:#f5f5f7;margin:0;padding:32px}main{max-width:900px;margin:auto}section{border:1px solid #333;border-radius:16px;padding:20px;margin:16px 0;background:#15151f}h1{color:#d4af37}a{color:#d4af37;margin-left:16px}</style></head><body><main><h1>🎬 DRAMA AI</h1><section><h2>Production Dashboard</h2><p>Discovery → Rights Review → Generation → Approval → Publish → Analytics.</p><p>Evidence Gate: no real artifact/receipt = no success.</p></section><section><h2>Live API</h2><p><a href='/api/health'>Health</a><a href='/api/stories'>Stories</a><a href='/api/agent-status'>Agent</a><a href='/api/publisher-status'>Publisher</a></p></section></main></body></html>"""

@app.get("/", response_class=HTMLResponse)
def production_root():
    return DASHBOARD

@app.get("/api", response_class=HTMLResponse)
def production_api_root():
    return DASHBOARD

@app.get("/api/health")
def production_health():
    return _health()

@app.get("/api/stories")
def production_stories():
    return _stories()

@app.get("/api/agent-status")
def production_agent():
    return _agent_status()

@app.get("/api/publisher-status")
def production_publisher():
    return _publisher_status()

@app.api_route("/{path:path}", methods=["GET"])
def production_fallback(path: str, request: Request):
    p = "/" + path.lstrip("/")
    if p.endswith("/health"):
        return _health()
    if p.endswith("/stories"):
        return _stories()
    if p.endswith("/agent-status"):
        return _agent_status()
    if p.endswith("/publisher-status"):
        return _publisher_status()
    if p in {"/", "/api", "/api/"}:
        return HTMLResponse(DASHBOARD)
    return JSONResponse({"detail":"Not Found"}, status_code=404)
