#!/usr/bin/env python -B

"""Example of rate-limiting your web server.

Caveat emptor: While the transfer rates imposed by this mechanism will
look accurate with wget's rate-meter, don't forget to examine your network
interface's traffic statistics as well.  The current implementation tends
to create lots of small packets in some conditions, and each packet carries
with it some bytes of overhead.  Check to make sure this overhead is not
costing you more bandwidth than you are saving by limiting the rate!
"""

from twisted.protocols import htb
from twisted.python import log
# for picklability
# from mcs import shaper

def gen_server_wide_token_bucket(server_rate, server_burst=None):

    if server_burst is None:
        server_burst = server_rate

    log.msg('server-wide bandwidth limit: %s bytes per second' % server_rate)
    log.msg('server-wide initial burst: %s bytes' % server_burst)

    serverFilter = htb.HierarchicalBucketFilter()
    serverBucket = htb.Bucket()

    serverBucket.maxburst = int(server_burst)
    serverBucket.rate = int(server_rate)

    serverFilter.buckets[None] = serverBucket
    
    return serverFilter

def gen_per_client_token_bucket(client_rate, client_burst=None):

    if client_burst is None:
        client_burst = client_rate

    log.msg('per-client bandwidth limit: %s bytes per second' % client_rate)
    log.msg('per-client initial burst: %s bytes' % client_burst)

    # Web service is also limited per-host:
    class WebClientBucket(htb.Bucket):
        maxburst = int(client_burst)
        rate = int(client_rate)

    return WebClientBucket

def gen_token_bucket(protocol, server_rate,       client_rate=None,
                               server_burst=None, client_burst=None):

    if client_rate is None:
        client_rate = server_rate

    serverFilter = gen_server_wide_token_bucket(server_rate, server_burst)

    webFilter = htb.FilterByHost(serverFilter)
    # for picklability
    # webFilter.bucketFactory = shaper.gen_per_client_token_bucket(client_rate, client_burst)
    webFilter.bucketFactory = gen_per_client_token_bucket(client_rate, client_burst)

    return htb.ShapedProtocolFactory(protocol, webFilter)

if __name__ == "__main__":
    import sys, os

    log.startLogging(sys.stdout)

    server_type = "web" # "chargen"
    server_port = 8080

    # Cap total server traffic at 20 kB/s
    server_burst=20000
    server_rate=20000 
    # Your first 10k is free
    client_burst=10000
    # One kB/s thereafter
    client_rate=1000

    len_sys_argv = len(sys.argv)
    if len_sys_argv > 1:
        server_type = sys.argv[1]
    if len_sys_argv > 2:
        server_port = int(sys.argv[2])
    if len_sys_argv > 3:
        server_rate = server_burst = int(sys.argv[3])
    if len_sys_argv > 4:
        client_rate = client_burst = int(sys.argv[4])
    if len_sys_argv > 5:
        server_burst = int(sys.argv[5])
    if len_sys_argv > 6:
        client_burst = int(sys.argv[6])

    if server_type == "web":
        from twisted.web import server, static
        site = server.Site(static.File(os.path.abspath(os.getcwd())))
        site.protocol = gen_token_bucket(site.protocol, server_rate,  client_rate,
                                                        server_burst, client_burst)
    elif server_type == "chargen":
        from twisted.protocols import wire
        from twisted.internet import protocol
        site = protocol.ServerFactory()
        site.protocol = gen_token_bucket(wire.Chargen, server_rate,  client_rate,
                                                       server_burst, client_burst)
        #site.protocol = wire.Chargen
    else:
        sys.exit("Unknown server-type '%s'. "
                 "Only 'web' and 'chargen' are supported." % server_type)

    from twisted.internet import reactor
    reactor.listenTCP(server_port, site)
    reactor.run()
