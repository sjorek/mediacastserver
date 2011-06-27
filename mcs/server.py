# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.

"""
Support for creating a service which runs a web server.
"""

import sys, os

# Twisted Imports

from twisted.python import log, usage
from twisted.web import distrib, rewrite, server, vhost
from twisted.internet import interfaces
from twisted.application import service, strports

from mcs import alias, bonjour, shaper, static

class Options(usage.Options):
    """
    Define the options accepted by the I{twistd web} plugin.
    """
    synopsis = "[mediacastserver options]"

    optParameters = [["logfile", "l", None, "Path to web CLF (Combined Log Format) log file."],
                     ]

    optFlags = [["notracebacks", "n", "Display tracebacks in broken web pages. " + 
                 "Displaying tracebacks to users may be security risk!"],
                ]

    zsh_actions = {"logfile" : "_files -g '*.log'"}


    longdesc = """\
This starts a webserver, intended to serve from a filesystem."""

    def __init__(self):
        usage.Options.__init__(self)
        self['hosts'] = [{'indexes': [],
                          'aliases': [],
                          'vhosts': [],
                          'root': None,
                          'shape': None,
                          'port': None
                          }]


    def opt_port(self, portStr):
        """strports description of the port to
        start the server on."""
        self['hosts'][0]['port'] = portStr

    opt_p = opt_port


    def opt_host(self, portStr):
        """port number (not strports description!) to
        start an additional server on."""
        self['hosts'].append({'indexes': [],
                              'aliases': [],
                              'vhosts': [],
                              'root': None,
                              'shape': None,
                              'port': 'tcp:%d' % int(portStr)
                              })

    opt_h = opt_host


    def opt_vhost(self, fqdn):
        """Additional vhost(s) to run, eg.:
        host.domain.tld
        """
        self['hosts'][-1]['vhosts'].append({'fqdn':fqdn,
                                            'root':None,
                                            'indexes':[],
                                            'aliases':[]})

    opt_v = opt_vhost


    def opt_index(self, indexName):
        """Add the name of a file used to check for directory indexes.
        [default: index, index.html]
        """
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
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
        alias = alias.rewrite(aliasPath.strip(), destPath.strip())
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        cfg['aliases'].append(alias)

    opt_a = opt_alias


    def opt_user(self):
        """Makes a server with ~/public_html and ~/.twistd-web-pb support for
        users.
        """
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        cfg['root'] = distrib.UserDirectory()

    opt_u = opt_user


    def opt_path(self, path):
        """
        <path> is either a specific file or a directory to be set as the root
        of the web server.
        """
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        cfg['root'] = static.File(os.path.abspath(path))

    def opt_mime_type(self, defaultType):
        """Specify the default mime-type for static files."""
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        if not isinstance(cfg['root'], static.File):
            raise usage.UsageError("You can only use --mime_type "
                                   "after --path.")
        cfg['root'].defaultType = defaultType

    opt_m = opt_mime_type


    def opt_allow_ignore_ext(self):
        """Specify whether or not a request for 'foo' should return 'foo.ext'"""
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        if not isinstance(cfg['root'], static.File):
            raise usage.UsageError("You can only use --allow_ignore_ext "
                                   "after --path.")
        cfg['root'].ignoreExt('*')

    def opt_ignore_ext(self, ext):
        """Specify an extension to ignore.  These will be processed in order.
        """
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        if not isinstance(cfg['root'], static.File):
            raise usage.UsageError("You can only use --ignore_ext "
                                   "after --path.")
        cfg['root'].ignoreExt(ext)


    def opt_shape(self, limitMap):
        """Limit download bandwidth server-wide, optionally with server-wide
        initial burst, per client-connection rate-limit and per client-connection
        initial burst: 
        server-wide-rate[:per-client-rate[:server-wide-burst[:per-client-burst]]]
        """
        limit = [limitMap]
        if ":" in limitMap:
            limit = limitMap.split(":", 4)
        self['hosts'][-1]['shape'] = limit

    opt_s = opt_shape


    def postOptions(self):
        """
        Set up conditional defaults and check for dependencies.

        If no server port was supplied, select a default appropriate for the
        other options supplied.
        """
        if self['hosts'][0]['port'] is None:
            self['hosts'][0]['port'] = 'tcp:8080'

        ports = {}
        for host_config in self['hosts']:
            if ports.has_key(host_config['port']):
                raise usage.UsageError("Duplicate port definition: %s" %
                                       host_config['port'])
            ports[host_config['port']] = True
        del ports


def makeService(config):
    computername = unicode(os.popen("/usr/sbin/networksetup -getcomputername",
                                    "r").readlines()[0]).strip()
    s = service.MultiService()

    for host_config in config['hosts']:
        if host_config['root'] is None:
            host_config['root'] = static.File(os.path.abspath(os.getcwd()))

        if host_config['indexes']:
            host_config['root'].indexNames = host_config['indexes']

        if isinstance(host_config['root'], static.File):
            host_config['root'].registry.setComponent(interfaces.IServiceCollection, s)

        if host_config['aliases']:
            host_config['root'] = rewrite.RewriterResource(host_config['root'],
                                                           *host_config['aliases'])

        if host_config['vhosts']:

            vhost_root = vhost.NameVirtualHost()
            vhost_root.default = host_config['root']

            for vhost_config in host_config['vhosts']:
                if vhost_config['root'] is None:
                    vhost_config['root'] = static.File(os.path.abspath(os.getcwd()))
                
                if vhost_config['indexes']:
                    vhost_config['root'].indexNames = vhost_config['indexes']

                if isinstance(vhost_config['root'], static.File):
                    vhost_config['root'].registry.setComponent(interfaces.IServiceCollection, s)

                if vhost_config['aliases']:
                    vhost_config['root'] = rewrite.RewriterResource(vhost_config['root'],
                                                                    *vhost_config['aliases'])

                vhost_root.addHost(vhost_config['fqdn'], vhost_config['root'])

            host_config['root'] = vhost_root

        if config['logfile']:
            site = server.Site(host_config['root'], logPath=config['logfile'])
        else:
            site = server.Site(host_config['root'])

        site.displayTracebacks = not config["notracebacks"]

        if not host_config['shape'] is None:
            site.protocol = shaper.gen_token_bucket(site.protocol,
                                                    *host_config['shape'])

        port = host_config['port']
        if ":" in str(host_config['port']):
            port = host_config['port'].split(':', 2)[1]

        root_mdns = bonjour.mDNSService(u"Mediacast-Webserver (%s on port %s)" % 
                                        (computername, port), "_http._tcp", int(port))
        root_mdns.setServiceParent(s)

        strports.service(host_config['port'], site).setServiceParent(s)

    return s
