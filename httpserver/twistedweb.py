"""
This is an .tac file which starts a webserver on port 8080 and
serves files from the current working directory.

The important part of this, the part that makes it a .tac file, is
the final root-level section, which sets up the object called 'application'
which twistd will look for
"""

import sys, os
from twisted.application import service, internet
from twisted.web import static, server

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from httpserver import mediatypes

SERVE_PATH = os.getcwd()
SERVE_PORT = 8080

class File(static.File):
    __doc__ = static.File.__doc__
    
    contentTypes = static.File.contentTypes
    contentTypes.update(mediatypes.VIDEO_MIME_TYPES)
    
    def __init__(self, path, defaultType=mediatypes.DEFAULT_MIME_TYPE,
                 ignoredExts=(), registry=None, allowExt=0):
        """Create a file with the given path.
        """
        static.File.__init__(self, path=path, defaultType=defaultType,
                             ignoredExts=ignoredExts, registry=registry,
                             allowExt=allowExt)
    
    def upgradeToVersion2(self):
        self.defaultType = mediatypes.DEFAULT_MIME_TYPE

def getWebService():
    """
    Return a service suitable for creating an application object.

    This service is a simple web server that serves files on port 8080 from
    underneath the current working directory.
    """
    # create a resource to serve static files
    factory = server.Site(File(SERVE_PATH))
    return internet.TCPServer(SERVE_PORT, factory)

# this is the core part of any tac file, the creation of the root-level
# application object
webapp = service.Application("web server")

# attach the service to its parent application
webservice = getWebService()
webservice.setServiceParent(webapp)
