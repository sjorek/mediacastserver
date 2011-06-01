#!/usr/bin/env python -B

import mimetypes
import BaseHTTPServer
import SimpleHTTPServer
import video_mime_types

class StreamHTTPRequestHandler(SimpleHTTPServer.SimpleHTTPRequestHandler):
    if not mimetypes.inited:
        mimetypes.init() # try to read system mime.types
    extensions_map = mimetypes.types_map.copy()
    extensions_map.update({'': video_mime_types.DEFAULT_MIME_TYPE}) # Default
    extensions_map.update(video_mime_types.VIDEO_MIME_TYPES)

if __name__ == "__main__":
    SimpleHTTPServer.test(HandlerClass=StreamHTTPRequestHandler,
                          ServerClass=BaseHTTPServer.HTTPServer)
