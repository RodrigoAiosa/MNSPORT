import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.dirname(_HERE)):  # api/ (para _common) e raiz (para mnsport)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from http.server import BaseHTTPRequestHandler

from _common import load, respond


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        respond(self, lambda: [m.as_dict() for m in load(self.path)])
