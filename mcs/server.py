# © copyright 2011-2013 Stephan Jorek <stephan.jorek@gmail.com>.
# See LICENSE for details.

"""
Create a service which runs a web server.
"""

import os
import warnings
# Twisted Imports

from twisted.python import usage
from twisted.web import distrib, error, proxy, rewrite, server, vhost
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
        self['hosts'] = [{
                          'root': None,
                          'shape': None,
                          'port': None,
                          'bonjour': [],
                          'indexes': [],
                          'aliases': [],
                          'vhosts': [],
                          'leafs': {}
                          }]


    def opt_port(self, portStr):
        """strports description of the port to
        start the server on."""
        self['hosts'][0]['port'] = portStr

    opt_p = opt_port


    def opt_host(self, portStr):
        """port number (not strports description!) to
        start an additional server on."""
        self['hosts'].append({'root': None,
                              'shape': None,
                              'port': 'tcp:%d' % int(portStr),
                              'bonjour': [],
                              'indexes': [],
                              'aliases': [],
                              'vhosts': [],
                              'leafs': {}
                              })

    opt_h = opt_host


    def opt_vhost(self, fqdn):
        """Additional vhost(s) to run, eg.:
        host.domain.tld
        """
        self['hosts'][-1]['vhosts'].append({'root':None,
                                            'fqdn':fqdn,
                                            'indexes':[],
                                            'aliases':[],
                                            'leafs': {}
                                            })

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
        alias/path[,real/path]
        """
        aliasPath = aliasMap
        destPath = ''
        if "," in aliasMap:
            aliasPath, destPath = aliasMap.split(",", 2)
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
        server-wide-rate[,per-client-rate[,server-wide-burst[,per-client-burst]]]
        """
        limit = [limitMap]
        if "," in limitMap:
            limit = limitMap.split(",", 4)
        self['hosts'][-1]['shape'] = limit

    opt_s = opt_shape


    def opt_reverse(self, proxyStr):
        """run a reverse proxy, either as the whole server or on a direct
        child-path (leaf) only eg.:
        host.domain.tld[,port-number[,path/to/proxy[,path/on/this/server]]]"""
        proxyCfg = proxyStr.split(',', 4)

        host = proxyCfg[0]

        if len(proxyCfg) > 1:
            port = int(proxyCfg[1])
        else:
            port = 80

        if len(proxyCfg) > 2:
            path = proxyCfg[2]
        else:
            path = ''

        if len(proxyCfg) > 3:
            leaf = proxyCfg[3]
        else:
            leaf = None

        res = proxy.ReverseProxyResource(host, port, path)

        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        if leaf is None:
            cfg['root'] = res
        else:
            cfg['leafs'].setdefault(leaf, res)


    def opt_monster(self, monsterPath):
        """add a vhost monster child-path intended to connect a reverse proxy.

        This makes it possible to put it behind a reverse proxy transparently.
        Just have the reverse proxy proxy to

            host,port,/vhost-monster-child-path/http/external-host:port/

        and on redirects and other link calculation, the external-host:port
        will be transmitted to this client."""
        cfg = self['hosts'][-1]
        if self['hosts'][-1]['vhosts']:
            cfg = self['hosts'][-1]['vhosts'][-1]
        cfg['leafs'].setdefault(monsterPath, vhost.VHostMonsterResource())


    def opt_bonjour(self, bonjourStr):
        """override or append additional bonjour (mDNS/zeroconf) record.  the
        first occurrence per host overrides the default description, subsequent
        occurrences append additional records.  eg.:
        'computer %s on port %d'"""
        self['hosts'][-1]['bonjour'].append(unicode(bonjourStr))


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

def prepareMultiService(multi_service, config):

    if config['root'] is None:
        config['root'] = static.File(os.path.abspath(os.getcwd()))

    if config['indexes']:
        config['root'].indexNames = config['indexes']

    for path, res in config['leafs'].iteritems():
        segments = path.split('/')
        print 'path %s segs %s' % (path,segments), config['root']
        parent = config['root']
        for segment in range(0, len(segments) - 1, 1):
            child = parent.getChildWithDefault(segments[segment], None)
            if isinstance(child, error.NoResource):
                child = static.PathSegment()
                parent.putChild(segments[segment], child)
            elif segment > 0 and not isinstance(static.Data):
                warnings.warn("path '%s' might not work." % path)
            parent = child
        if isinstance(parent.getChildWithDefault(segments[-1], None),
                      error.NoResource):
            parent.putChild(segments[-1], res)
        else:
            warnings.warn("ignoring path '%s', as it is already defined." % path)

    if isinstance(config['root'], static.File):
        config['root'].registry.setComponent(interfaces.IServiceCollection,
                                             multi_service)

    if config['aliases']:
        config['root'] = rewrite.RewriterResource(config['root'],
                                                  *config['aliases'])

def makeService(config):
    computername = unicode(os.popen("/usr/sbin/networksetup -getcomputername",
                                    "r").readlines()[0]).strip()
    s = service.MultiService()

    for host_config in config['hosts']:

        prepareMultiService(s, host_config)

        if host_config['vhosts']:

            vhost_root = vhost.NameVirtualHost()
            vhost_root.default = host_config['root']

            for vhost_config in host_config['vhosts']:

                prepareMultiService(s, vhost_config)

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
        port = int(port)

        if not host_config['bonjour']:
            host_config['bonjour'].append(u"Mediacast-Webserver (%s on port %d)")

        for bonjour_desc in host_config['bonjour']:
            if '%s' in bonjour_desc and '%d' in bonjour_desc:
                bonjour_desc %= (computername, port)
            elif '%s' in bonjour_desc:
                bonjour_desc %= computername
            elif '%d' in bonjour_desc:
                bonjour_desc %= port
            bonjour.mDNSService(bonjour_desc, "_http._tcp", port).setServiceParent(s)

        strports.service(host_config['port'], site).setServiceParent(s)

    return s
