#!/usr/bin/env python3
import http.server
import os
import sys

port = int(sys.argv[1]) if len(sys.argv) > 1 else 8787
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '_site'))
print(f"Serving _site on http://localhost:{port}")
http.server.test(HandlerClass=http.server.SimpleHTTPRequestHandler, port=port)
