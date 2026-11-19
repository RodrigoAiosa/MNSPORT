from http.server import BaseHTTPRequestHandler

from _common import load, respond


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        respond(self, lambda: [m.as_dict() for m in load(self.path)])
