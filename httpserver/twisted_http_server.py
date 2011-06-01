#!/usr/bin/env python -B

import sys, os
from twisted.web.server import Site
from twisted.web.static import File
from twisted.internet import reactor

import mediatypes

SERVE_PATH = len(sys.argv) > 1 and sys.argv[1] or os.getcwd()
SERVE_PORT = len(sys.argv) > 2 and sys.argv[2] or 8080

resource = File(SERVE_PATH)
resource.defaultType = mediatypes.DEFAULT_MIME_TYPE
resource.contentTypes.update(mediatypes.VIDEO_MIME_TYPES)

factory = Site(resource)

if __name__ == "__main__":
    print 'running webserver for path "%s" on port %d' % (SERVE_PATH, SERVE_PORT)
    reactor.listenTCP(SERVE_PORT, factory)
    reactor.run()
