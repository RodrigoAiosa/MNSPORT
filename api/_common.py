import json
import os
import sys
from urllib.parse import urlparse, parse_qs

os.environ.setdefault("MNSPORT_CACHE", "/tmp/mnsport")  # FS da Vercel é somente leitura fora de /tmp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from mnsport import sources  # noqa: E402
from mnsport.parser import parse_footballtxt  # noqa: E402


def load(path):
    q = {k: v[0] for k, v in parse_qs(urlparse(path).query).items()}
    season = int(q.get("season", 2025))
    division = q.get("division", "br1")
    ms = parse_footballtxt(sources.fetch_season(season, division))
    team = q.get("team", "").lower()
    if team:
        ms = [m for m in ms if team in m.home.lower() or team in m.away.lower()]
    return ms


def respond(handler, fn):
    try:
        body, status = json.dumps(fn(), ensure_ascii=False).encode(), 200
    except Exception as e:  # entrada inválida ou fonte indisponível
        body, status = json.dumps({"error": str(e)}).encode(), 400
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Cache-Control", "s-maxage=3600, stale-while-revalidate")
    handler.end_headers()
    handler.wfile.write(body)
