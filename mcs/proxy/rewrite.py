
from twisted.web import http, proxy

class RewriteProxyRequest(proxy.ProxyRequest):
    pass

class RewriteProxy(proxy.Proxy):
    requestFactory = RewriteProxyRequest

class RewriteProxyFactory(http.HTTPFactory):
    protocol = RewriteProxy