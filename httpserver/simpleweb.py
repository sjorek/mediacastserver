#!/usr/bin/env python

import sys, os
import mimetypes
import BaseHTTPServer
import SimpleHTTPServer

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import mediatypes

class StreamHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({'': mediatypes.DEFAULT_MIME_TYPE}) # Default
    extensions_map.update(mediatypes.VIDEO_MIME_TYPES)

if __name__ == "__main__":
    SimpleHTTPServer.test(HandlerClass=StreamHTTPRequestHandler,
                          ServerClass=BaseHTTPServer.HTTPServer)
