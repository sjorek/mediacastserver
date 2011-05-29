#!/usr/bin/env python -B

import mimetypes
import BaseHTTPServer
import SimpleHTTPServer

class StreamHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({
        '': 'application/octet-stream', # Default
        '.m3u8': 'application/x-mpegurl',
        '.ts': 'video/mp2t',
        '.ogv': 'video/ogg',
        '.mp4': 'video/mp4',
        '.m4v': 'video/mp4',
        '.webm': 'video/webm'
        })

if __name__ == "__main__":
    SimpleHTTPServer.test(HandlerClass=StreamHTTPRequestHandler,
                          ServerClass=BaseHTTPServer.HTTPServer)
