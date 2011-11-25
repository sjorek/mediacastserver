# Copyright (c) 2011 Stephan Jorek <stephan.jorek@gmail.com>.
# See LICENSE for details.

# import sys, os

from twisted.application import service
from twisted.internet import reactor
from twisted.internet.defer import Deferred
from twisted.internet.interfaces import IReadDescriptor
from twisted.python import log
from zope import interface

# d = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
# sys.path.insert(0, os.path.abspath(os.path.join(d, os.pardir, 'pybonjour')))
# del d
try:
    import pybonjour
except ImportError:
    print "pybonjour-library missing in %s" % __file__
    exit(1);

class mDNSServiceDescriptor(object):
    """
    Glue for integrating a pybonjour service with twisted.
    See: http://www.indelible.org/ink/twisted-bonjour/
    """

    interface.implements(IReadDescriptor)

    def __init__(self, sdref):
        self.sdref = sdref

    def doRead(self):
        pybonjour.DNSServiceProcessResult(self.sdref)

    def fileno(self):
        return self.sdref.fileno()

    def logPrefix(self):
        return "bonjour"

    def connectionLost(self, reason):
        log.msg('Connection lost, unregistering advertised service')
        self.sdref.close()

class mDNSService(service.Service):
    """
    Bonjour broadcasting encapsulated in a Twisted Service.
    """

    mdns_sdref = None
    mdns_type = None
    mdns_port = None

    def __init__(self, name, regtype, port):
        self.setName(name)
        self.mdns_sdref = None
        self.mdns_type = regtype
        self.mdns_port = port

    def startService(self):
        log.msg("Starting mDNS service: %s" % self.name)
        me = self
        def _success(args):
            me.mdns_sdref  = args[0]
            log.msg('Registered mDNS service: %s.%s%s' % args[1:])

        def _failed(errorCode):
            log.err('Error while registering mDNS service: %s' % self.name)
            log.err(errorCode)

        self.mDNSServiceRegister(_success, _failed)
        service.Service.startService(self)

    def mDNSServiceRegister(self, _callback, _errback):

        d = Deferred()
        d.addCallback(_callback)
        d.addErrback(_errback)

        def _callback(sdref, flags, errorCode, name, regtype, domain):
            if errorCode == pybonjour.kDNSServiceErr_NoError:
                d.callback((sdref, name, regtype, domain))
            else:
                d.errback(errorCode)

        self.mdns_sdref = pybonjour.DNSServiceRegister(name=self.name,
                                                       regtype=self.mdns_type,
                                                       port=self.mdns_port,
                                                       callBack=_callback)

        reactor.addReader(mDNSServiceDescriptor(self.mdns_sdref))

        return d

    def stopService(self):
        log.msg("Stopping mDNS service: %s" % self.name)
        service.Service.stopService(self)
