from http.server import BaseHTTPRequestHandler

from _common import load, respond
from mnsport.parser import standings


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        respond(self, lambda: standings(load(self.path)))
