#!/usr/bin/env python

import mimetypes
import BaseHTTPServer
import SimpleHTTPServer

class StreamHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.m3u8': 'application/x-mpegURL',
        '.ts': 'video/MP2T'
        })

if __name__ == "__main__":
    SimpleHTTPServer.test(HandlerClass=StreamHTTPRequestHandler,
                          ServerClass=BaseHTTPServer.HTTPServer)
