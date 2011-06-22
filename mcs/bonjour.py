import sys, os

from twisted.application import service
from twisted.python import log
from twisted.internet.interfaces import IReadDescriptor
from zope import interface

d = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(d, os.pardir, 'pybonjour')))
del d

import pybonjour


class ServiceDescriptor(object):

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
        self.sdref.close()

class Service(service.Service):

#    mdns_name  = None
#    mdns_type  = None
#    mdns_port  = None
#    mdns_sdref = None
#
#    def __init__(self, name, regtype, port):
#        self.mdns_name = name
#        self.mdns_type = regtype
#        self.mdns_port = port

    def startService(self):
        log.msg("%s service starting" % self.name)
        service.Service.startService(self)
#        self.mdns_sdref = pybonjour.DNSServiceRegister(name = self.mdns_name,
#                                                       regtype = self.mdns_type,
#                                                       port = self.mdns_port,
#                                                       callBack = self.mDNSregisterCallback)

    def stopService(self):
        log.msg("%s service stopping" % self.name)
        service.Service.stopService(self)

#    def mDNSregisterCallback(self, sdRef, flags, errorCode, name, regtype, domain):
#        if errorCode == pybonjour.kDNSServiceErr_NoError:
#            print '%s registered service:' % self.__class__.__name__
#            print '  name    =', name
#            print '  regtype =', regtype
#            print '  domain  =', domain
#        else:
#            print '%s error while registering service: %s' % (self.__class__.__name__,
#                                                              errorCode)
