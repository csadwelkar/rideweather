#!/usr/bin/env python3
"""RideWeather — route weather planner for Ride with GPS routes."""

import json
import re
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse

import os

PORT = int(os.environ.get("PORT", 8765))

HTML = open("index.html", encoding="utf-8").read()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html()
        elif parsed.path == "/api/route":
            self._proxy_route(parsed.query)
        else:
            self.send_response(404)
            self.end_headers()

    def _html(self):
        body = HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _proxy_route(self, qs):
        params = parse_qs(qs)
        route_id = params.get("id", [None])[0]
        if not route_id or not re.match(r"^\d+$", route_id):
            self._err(400, "Invalid route ID")
            return
        try:
            url = f"https://ridewithgps.com/routes/{route_id}.json"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 RideWeather/1.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                body = r.read()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            self.wfile.write(body)
        except urllib.error.HTTPError as e:
            self._err(e.code, f"Route fetch failed: {e.reason}")
        except Exception as e:
            self._err(500, str(e))

    def _err(self, code, msg):
        body = json.dumps({"error": msg}).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt, *args):
        pass  # suppress default logging


if __name__ == "__main__":
    server = HTTPServer(("0.0.0.0", PORT), Handler)
    print(f"🚴  RideWeather  →  http://0.0.0.0:{PORT}")
    server.serve_forever()
