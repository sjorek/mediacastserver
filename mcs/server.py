# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Support for creating a service which runs a web server.
"""

import os

# Twisted Imports
from twisted.web import distrib, rewrite, server, static, vhost
from twisted.internet import interfaces
from twisted.python import log, usage
from twisted.application import internet, service, strports
from mcs import bonjour, mediatypes, shaper

def rewrite_alias(aliasPath, destPath):
    """
    Original implementation in twisted.web.rewrite.alias.  This one
    supports an empty alias destination.
    
    I am not a very good aliaser. But I'm the best I can be. If I'm
    aliasing to a Resource that generates links, and it uses any parts
    of request.prepath to do so, the links will not be relative to the
    aliased path, but rather to the aliased-to path. That I can't
    alias static.File directory listings that nicely. However, I can
    still be useful, as many resources will play nice.
    """
    aliasPath = aliasPath.split('/')
    destPath = destPath.split('/')
    if destPath == ['']:
        def prepend_destPath(after):
            return after or ['']
    else:
        def prepend_destPath(after):
            return destPath + after
    def rewriter(request):
        if request.postpath[:len(aliasPath)] == aliasPath:
            after = request.postpath[len(aliasPath):]
            request.postpath = prepend_destPath(after)
            request.path = '/' + '/'.join(request.prepath + request.postpath)
    return rewriter


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

class Options(usage.Options):
    """
    Define the options accepted by the I{twistd web} plugin.
    """
    synopsis = "[web options]"

    optParameters = [["port", "p", None, "strports description of the port to "
                      "start the server on."],
                     ["logfile", "l", None, "Path to web CLF (Combined Log Format) log file."],
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
        self['aliases'] = []
        self['vhosts'] = []
        self['root'] = None
        self['limit'] = None


    def opt_vhost(self, fqdn):
        """Additional vhost(s) to run, eg.:
        host.domain.tld
        """
        self['vhosts'].append({'fqdn':fqdn,
                               'root':None,
                               'indexes':[],
                               'aliases':[]})

    opt_v = opt_vhost


    def opt_index(self, indexName):
        """Add the name of a file used to check for directory indexes.
        [default: index, index.html]
        """
        cfg = self
        if self['vhosts']:
            cfg = self['vhosts'][-1]
        cfg['indexes'].append(indexName)

    opt_i = opt_index


    def opt_alias(self, aliasMap):
        """Alias(es) mapping a (virtual) path to a (real) path, eg.: 
        alias/path[:real/path]
        """
        aliasPath = aliasMap
        destPath = ''
        if ":" in aliasMap:
            aliasPath, destPath = aliasMap.split(":", 2)
        alias = rewrite_alias(aliasPath.strip(), destPath.strip())
        cfg = self
        if self['vhosts']:
            cfg = self['vhosts'][-1]
        cfg['aliases'].append(alias)

    opt_a = opt_alias


    def opt_user(self):
        """Makes a server with ~/public_html and ~/.twistd-web-pb support for
        users.
        """
        cfg = self
        if self['vhosts']:
            cfg = self['vhosts'][-1]
        cfg['root'] = distrib.UserDirectory()

    opt_u = opt_user


    def opt_path(self, path):
        """
        <path> is either a specific file or a directory to be set as the root
        of the web server.
        """
        cfg = self
        if self['vhosts']:
            cfg = self['vhosts'][-1]
        cfg['root'] = File(os.path.abspath(path))

    def opt_mime_type(self, defaultType):
        """Specify the default mime-type for static files."""
        cfg = self
        if self['vhosts']:
            cfg = self['vhosts'][-1]
        if not isinstance(cfg['root'], File):
            raise usage.UsageError("You can only use --mime_type "
                                   "after --path.")
        cfg['root'].defaultType = defaultType

    opt_m = opt_mime_type


    def opt_allow_ignore_ext(self):
        """Specify whether or not a request for 'foo' should return 'foo.ext'"""
        cfg = self
        if self['vhosts']:
            cfg = self['vhosts'][-1]
        if not isinstance(cfg['root'], File):
            raise usage.UsageError("You can only use --allow_ignore_ext "
                                   "after --path.")
        cfg['root'].ignoreExt('*')

    def opt_ignore_ext(self, ext):
        """Specify an extension to ignore.  These will be processed in order.
        """
        cfg = self
        if self['vhosts']:
            cfg = self['vhosts'][-1]
        if not isinstance(cfg['root'], File):
            raise usage.UsageError("You can only use --ignore_ext "
                                   "after --path.")
        cfg['root'].ignoreExt(ext)


    def opt_limit(self, limitMap):
        """Limit download bandwidth server-wide, optionally with server-wide
        initial burst and per client-connection rate-limit and initial burst: 
        server-wide-rate[:per-client-rate[:server-wide-burst[:per-client-burst]]]
        """
        limit = [limitMap]
        if ":" in limitMap:
            limit = limitMap.split(":", 4)
        self['limit'] = limit


    def postOptions(self):
        """
        Set up conditional defaults and check for dependencies.

        If no server port was supplied, select a default appropriate for the
        other options supplied.
        """
        if self['port'] is None:
            self['port'] = 'tcp:8080'

def makeService(config):
    s = service.MultiService()
    if config['root'] is None:
        config['root'] = File(os.path.abspath(os.getcwd()))

    if config['indexes']:
        config['root'].indexNames = config['indexes']

    if isinstance(config['root'], File):
        config['root'].registry.setComponent(interfaces.IServiceCollection, s)

    if config['aliases']:
        config['root'] = rewrite.RewriterResource(config['root'],
                                                  *config['aliases'])

    if config['vhosts']:

        vhost_root = vhost.NameVirtualHost()
        vhost_root.default = config['root']

        for vhost_config in config['vhosts']:
            if vhost_config['root'] is None:
                vhost_config['root'] = File(os.path.abspath(os.getcwd()))
            
            if vhost_config['indexes']:
                vhost_config['root'].indexNames = vhost_config['indexes']

            if isinstance(vhost_config['root'], File):
                vhost_config['root'].registry.setComponent(interfaces.IServiceCollection, s)

            if vhost_config['aliases']:
                vhost_config['root'] = rewrite.RewriterResource(vhost_config['root'],
                                                                *vhost_config['aliases'])

            vhost_root.addHost(vhost_config['fqdn'], vhost_config['root'])

        config['root'] = vhost_root

    root = config['root']

    if config['logfile']:
        site = server.Site(root, logPath=config['logfile'])
    else:
        site = server.Site(root)

    site.displayTracebacks = not config["notracebacks"]

    if not config['limit'] is None:
        site.protocol = shaper.gen_token_bucket(site.protocol, *config['limit'])

    port = config['port']
    if ":" in str(config['port']):
        port = config['port'].split(':', 2)[1]

    computername = unicode(os.popen("/usr/sbin/networksetup -getcomputername",
                                    "r").readlines()[0]).strip()

    root_mdns = bonjour.mDNSService(u"Mediacast-Webserver (%s on port %s)" % 
                                    (computername,port), "_http._tcp", int(port))
    root_mdns.setServiceParent(s)

    strports.service(config['port'], site).setServiceParent(s)

    return s
