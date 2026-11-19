import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
for _p in (_HERE, os.path.dirname(_HERE)):  # api/ (para _common) e raiz (para mnsport)
    if _p not in sys.path:
        sys.path.insert(0, _p)

from http.server import BaseHTTPRequestHandler

from _common import load, params, respond
from mnsport.forecast import title_probabilities
from mnsport.parser import standings


def build(path):
    matches = load(path)
    rows = standings(matches)
    if params(path).get("division", "br1") != "brcup":  # mata-mata não tem pontos corridos
        probs, as_of = title_probabilities(matches)
        if probs:
            for r in rows:
                r["p_title"] = probs.get(r["team"], 0.0)
                r["as_of"] = as_of
    return rows


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        respond(self, lambda: build(self.path))
