#!/usr/bin/env python -B

import sys, os
from twisted.web import server, static
from twisted.internet import reactor
from twisted.protocols import policies

import mediatypes

SERVE_PATH = len(sys.argv) > 1 and sys.argv[1] or os.getcwd()
SERVE_PORT = len(sys.argv) > 2 and int(sys.argv[2]) or 8080
SERVE_KBIT = len(sys.argv) > 3 and int(sys.argv[3]) or 112

class File(static.File):
    
    contentTypes = static.File.contentTypes
    contentTypes.update(mediatypes.VIDEO_MIME_TYPES)
    
    def __init__(self, path, defaultType=mediatypes.DEFAULT_MIME_TYPE,
                 ignoredExts=(), registry=None, allowExt=0):
        """Create a file with the given path.
        """
        static.File.__init__(self, path=path, defaultType=defaultType,
                             ignoredExts=ignoredExts, registry=registry,
                             allowExt=allowExt)

resource = File(SERVE_PATH)
factory = server.Site(resource)

SERVE_LIMIT = ''
if SERVE_KBIT > 0:
    SERVE_LIMIT = 'limited to %d kbits' % SERVE_KBIT
    factory = policies.ThrottlingFactory(factory, writeLimit=SERVE_KBIT * 128)

if __name__ == "__main__":
    print 'running webserver for path "%s" on port %d%s' % (SERVE_PATH,
                                                            SERVE_PORT,
                                                            SERVE_LIMIT)
    reactor.listenTCP(SERVE_PORT, factory)
    reactor.run()
