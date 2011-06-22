# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Support for creating a service which runs a web server.
"""

import os

# Twisted Imports
from twisted.web import server, static, distrib
from twisted.internet import interfaces
from twisted.python import usage
from twisted.application import internet, service, strports
from mcs import mediatypes

class StaticFile(static.File):
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

class Options(usage.Options):
    """
    Define the options accepted by the I{twistd web} plugin.
    """
    synopsis = "[web options]"

    optParameters = [["port", "p", None, "strports description of the port to "
                      "start the server on."],
                     ["logfile", "l", None, "Path to web CLF (Combined Log Format) log file."],
                     ["https", None, None, "Port to listen on for Secure HTTP."],
                     ["certificate", "c", "server.pem", "SSL certificate to use for HTTPS. "],
                     ["privkey", "k", "server.pem", "SSL certificate to use for HTTPS."],
                     ]

    optFlags = [["notracebacks", "n", "Display tracebacks in broken web pages. " + 
                 "Displaying tracebacks to users may be security risk!"],
                ]

    zsh_actions = {"logfile" : "_files -g '*.log'", "certificate" : "_files -g '*.pem'",
                   "privkey" : "_files -g '*.pem'"}


    longdesc = """\
This starts a webserver."""

    def __init__(self):
        usage.Options.__init__(self)
        self['indexes'] = []
        self['root'] = None

    def opt_index(self, indexName):
        """Add the name of a file used to check for directory indexes.
        [default: index, index.html]
        """
        self['indexes'].append(indexName)

    opt_i = opt_index

    def opt_user(self):
        """Makes a server with ~/public_html and ~/.twistd-web-pb support for
        users.
        """
        self['root'] = distrib.UserDirectory()

    opt_u = opt_user

    def opt_path(self, path):
        """
        <path> is either a specific file or a directory to be set as the root
        of the web server.
        """

        self['root'] = StaticFile(os.path.abspath(path))


    def opt_mime_type(self, defaultType):
        """Specify the default mime-type for static files."""
        if not isinstance(self['root'], StaticFile):
            raise usage.UsageError("You can only use --mime_type after --path.")
        self['root'].defaultType = defaultType

    opt_m = opt_mime_type


    def opt_allow_ignore_ext(self):
        """Specify whether or not a request for 'foo' should return 'foo.ext'"""
        if not isinstance(self['root'], StaticFile):
            raise usage.UsageError("You can only use --allow_ignore_ext "
                                   "after --path.")
        self['root'].ignoreExt('*')

    def opt_ignore_ext(self, ext):
        """Specify an extension to ignore.  These will be processed in order.
        """
        if not isinstance(self['root'], StaticFile):
            raise usage.UsageError("You can only use --ignore_ext "
                                   "after --path.")
        self['root'].ignoreExt(ext)

    def postOptions(self):
        """
        Set up conditional defaults and check for dependencies.

        If SSL is not available but an HTTPS server was configured, raise a
        L{UsageError} indicating that this is not possible.

        If no server port was supplied, select a default appropriate for the
        other options supplied.
        """
        if self['https']:
            try:
                from twisted.internet.ssl import DefaultOpenSSLContextFactory
            except ImportError:
                raise usage.UsageError("SSL support not installed")
        if self['port'] is None:
            self['port'] = 'tcp:8080'



def makeService(config):
    s = service.MultiService()
    if not config['root']:
        config['root'] = StaticFile(os.path.abspath(os.getcwd()))
    root = config['root']

    if config['indexes']:
        config['root'].indexNames = config['indexes']

    if isinstance(root, StaticFile):
        root.registry.setComponent(interfaces.IServiceCollection, s)

    if config['logfile']:
        site = server.Site(root, logPath=config['logfile'])
    else:
        site = server.Site(root)

    site.displayTracebacks = not config["notracebacks"]

    if config['https']:
        from twisted.internet.ssl import DefaultOpenSSLContextFactory
        i = internet.SSLServer(int(config['https']), site,
                      DefaultOpenSSLContextFactory(config['privkey'],
                                                   config['certificate']))
        i.setServiceParent(s)
    strports.service(config['port'], site).setServiceParent(s)

    return s
