import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.dirname(_HERE)):  # api/ (para _common) e raiz (para mnsport)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from http.server import BaseHTTPRequestHandler

from _common import params, respond
from mnsport.players import team_players


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        q = params(self.path)
        respond(self, lambda: team_players(q.get("team", ""), int(q.get("season", 2025)), q.get("division", "br1")),
                ttl=43200)  # 12 h: poupa a cota diária da API-Football
