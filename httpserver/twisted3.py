"""
This is an .tac file which starts a throttled webserver on port 8080 and
serves files from the current working directory.

The important part of this, the part that makes it a .tac file, is
the final root-level section, which sets up the object called 'application'
which twistd will look for
"""

import sys, os
from twisted.application import service, internet
from twisted.internet import abstract
from twisted.python import log
from twisted.protocols import policies
from twisted.web import error, http, static, server

sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))

from httpserver import mediatypes

SERVE_PATH = os.getcwd()
SERVE_PORT = 8080
SERVE_LIMIT_KBITS_PER_SECOND = 112
SERVE_LIMIT_BYTES_PER_SECOND = SERVE_LIMIT_KBITS_PER_SECOND * 128 or abstract.FileDescriptor.bufferSize

class FileTransfer(static.FileTransfer):
    __doc__ = static.FileTransfer.__doc__
    
    paused = None
    
    def __init__(self, file, size, request):
        self.paused = False
        self.file = file
        self.size = size
        self.request = request
        self.written = self.file.tell()
        request.registerProducer(self, 0)
    
    def resumeProducing(self):
        if self.paused or not self.request:
            return
        log.msg('%s resumed producing' % self)
        data = self.file.read(min(SERVE_LIMIT_BYTES_PER_SECOND,
                                  abstract.FileDescriptor.bufferSize,
                                  self.size - self.written))
        if data:
            self.written += len(data)
            # this .write will spin the reactor, calling .doWrite and then
            # .resumeProducing again, so be prepared for a re-entrant call
            self.request.write(data)
        if self.request and self.file.tell() == self.size:
            self.request.unregisterProducer()
            self.request.finish()
            self.request = None
    
    def pauseProducing(self):
        log.msg('%s paused producing' % self)
        self.paused = True
    
    def unpauseProducing(self):
        log.msg('%s unpaused producing' % self)
        self.paused = False

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
    
    def render(self, request):
        """You know what you doing."""
        self.restat()

        if self.type is None:
            self.type, self.encoding = static.getTypeAndEncoding(self.basename(),
                                                                 self.contentTypes,
                                                                 self.contentEncodings,
                                                                 self.defaultType)

        if not self.exists():
            return self.childNotFound.render(request)

        if self.isdir():
            return self.redirect(request)

        request.setHeader('accept-ranges', 'bytes')

        if self.type:
            request.setHeader('content-type', self.type)
        if self.encoding:
            request.setHeader('content-encoding', self.encoding)

        try:
            f = self.openForReading()
        except IOError, e:
            import errno
            if e[0] == errno.EACCES:
                return error.ForbiddenResource().render(request)
            else:
                raise

        if request.setLastModified(self.getmtime()) is http.CACHED:
            return ''

        # set the stop byte, and content-length
        contentLength = stop = self.getFileSize()

        byteRange = request.getHeader('range')
        if byteRange is not None:
            try:
                start, contentLength, stop = self._doRangeRequest(
                    request, self._parseRangeHeader(byteRange))
            except ValueError, e:
                log.msg("Ignoring malformed Range header %r" % (byteRange,))
                request.setResponseCode(http.OK)
            else:
                f.seek(start)

        request.setHeader('content-length', str(contentLength))
        if request.method == 'HEAD':
            return ''

        # return data
        FileTransfer(f, stop, request)
        # and make sure the connection doesn't get closed
        return server.NOT_DONE_YET

class ThrottlingProtocol(policies.ThrottlingProtocol):
    __doc__ = policies.ThrottlingProtocol.__doc__
    
    def unthrottleWrites(self):
        if hasattr(self, "producer"):
            if hasattr(self.producer, "unpauseProducing"):
                self.producer.unpauseProducing()
            self.producer.resumeProducing()

class ThrottlingFactory(policies.ThrottlingFactory):
    __doc__ = policies.ThrottlingFactory.__doc__
    
    protocol = ThrottlingProtocol

def getWebService():
    """
    Return a service suitable for creating an application object.

    This service is a simple web server that serves files on port 8080 from
    underneath the current working directory.
    """
    # create a resource to serve static files
    factory = server.Site(File(SERVE_PATH))
    if SERVE_LIMIT_KBITS_PER_SECOND > 0:
        factory = ThrottlingFactory(factory, writeLimit=SERVE_LIMIT_BYTES_PER_SECOND)
    return internet.TCPServer(SERVE_PORT, factory)

# this is the core part of any tac file, the creation of the root-level
# application object
webapp = service.Application("(Write-)Bandwidth throttled web server")

# attach the service to its parent application
webservice = getWebService()
webservice.setServiceParent(webapp)
