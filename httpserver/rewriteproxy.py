#! /usr/bin/env python

__revision__ = '$Rev$'

import sys, os 
import socket
import asyncore

d = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
sys.path.insert(0, os.path.abspath(os.path.join(d, os.path.pardir, 'throxy')))
sys.path.insert(0, os.path.abspath(d))
del d

import throxy

class Header(throxy.Header):
    
    rewrite_forward = {}
    rewrite_reverse = {}
    
    def extract_host(self):
        """Extract host and perform DNS lookup."""
        self.host = self.extract('Host')
        if self.host is None:
            return
        self.host = self.rewrite_forward.get(self.host, self.host)
        if self.host.count(':'):
            self.host_name, self.host_port = self.host.split(':')
            self.host_port = int(self.host_port)
        else:
            self.host_name = self.host
            self.host_port = 80
        self.host_ip = socket.gethostbyname(self.host_name)
        self.host_addr = (self.host_ip, self.host_port)
    
    def extract_request(self):
        """Extract path from HTTP request."""
        match = throxy.request_match(self.lines[0])
        if not match:
            raise ValueError("malformed request line " + self.lines[0])
        self.method, self.url, self.proto = match.groups()
        if self.method.upper() == 'CONNECT':
            raise ValueError("method CONNECT is not supported")
        prefix = 'http://' + self.rewrite_reverse.get(self.host, self.host)
        if not self.url.startswith(prefix):
            raise ValueError("URL doesn't start with " + prefix)
        self.path = self.url[len(prefix):]

class ClientChannel(throxy.ClientChannel):
    """A client connection."""

    def __init__(self, channel, addr, download_throttle, upload_throttle):
        throxy.ThrottleSender.__init__(self, download_throttle, channel)
        self.upload_throttle = upload_throttle
        self.addr = addr
        self.header = Header()
        self.content_length = 0
        self.server = None
        self.handle_connect()

    def handle_read(self):
        """Read some data from the client."""
        data = self.recv(8192)
        while len(data):
            if self.content_length:
                bytes = min(self.content_length, len(data))
                self.server.buffer.append(data[:bytes])
                if options.dump_send_content:
                    self.header.dump_content(
                        data[:bytes], self.addr, self.header.host_addr)
                data = data[bytes:]
                self.content_length -= bytes
            if not len(data):
                break
            if self.header.complete and self.content_length == 0:
                throxy.debug("client %s:%d sends a new request" % self.addr)
                self.header = Header()
                self.server = None
            data = self.header.append(data)
            if self.header.complete:
                self.content_length = int(
                    self.header.extract('Content-Length', 0))
                self.header.extract_host()
                if options.dump_send_headers:
                    self.header.dump(self.addr, self.header.host_addr)
                self.server = throxy.ServerChannel(
                    self, self.header, self.upload_throttle)

class ProxyServer(throxy.ProxyServer):
    """Listen for client connections."""
    def __init__(self):
        if options.rewrite_map:
            d = dict([m.split(';') for m in options.rewrite_map.split(',')])
            Header.rewrite_forward.update(d)
            Header.rewrite_reverse.update(dict(zip(d.values(), d.keys())))
        throxy.ProxyServer.__init__(self)
    
    def handle_accept(self):
        """Accept a new connection from a client."""
        channel, addr = self.accept()
        if addr[0] == '127.0.0.1' or options.allow_remote:
            ClientChannel(channel, addr,
                          self.download_throttle, self.upload_throttle)
        else:
            channel.close()
            throxy.debug("remote client %s:%d not allowed" % addr)

if __name__ == '__main__':
    from optparse import OptionParser
    version = '%prog ' + __revision__.strip('$').replace('Rev: ', 'r')
    parser = OptionParser(version=version)
    parser.add_option('-i', dest='interface', action='store', type='string',
        metavar='<ip>', default='',
        help="listen on this interface only (default all)")
    parser.add_option('-p', dest='port', action='store', type='int',
        metavar='<port>', default=8081,
        help="listen on this port number (default 8081)")
    parser.add_option('-d', dest='download', action='store', type='float',
        metavar='<kbps>', default=112.0,
        help="download bandwidth in kbps (default 112.0, aka. edge)")
    parser.add_option('-u', dest='upload', action='store', type='float',
        metavar='<kbps>', default=112.0,
        help="upload bandwidth in kbps (default 112.0, aka. edge)")
    parser.add_option('-o', dest='allow_remote', action='store_true',
        help="allow remote clients (WARNING: open proxy)")
    parser.add_option('-q', dest='quiet', action='store_true',
        help="don't show connect and disconnect messages")
    parser.add_option('-s', dest='dump_send_headers', action='store_true',
        help="dump headers sent to server")
    parser.add_option('-r', dest='dump_recv_headers', action='store_true',
        help="dump headers received from server")
    parser.add_option('-S', dest='dump_send_content', action='store_true',
        help="dump content sent to server")
    parser.add_option('-R', dest='dump_recv_content', action='store_true',
        help="dump content received from server")
    parser.add_option('-l', dest='text_dump_limit', action='store',
        metavar='<bytes>', type='int', default=1024,
        help="maximum length of dumped text content (default 1024)")
    parser.add_option('-L', dest='data_dump_limit', action='store',
        metavar='<bytes>', type='int', default=256,
        help="maximum length of dumped binary content (default 256)")
    parser.add_option('-g', dest='gzip_size_limit', action='store',
        metavar='<bytes>', type='int', default=8192,
        help="maximum size for gzip decompression (default 8192)")
    parser.add_option('-m', dest='rewrite_map', action='store',
        metavar='<map>', type='string', default='',
        help="host rewrite map, eg: www.some.tld;localhost:8080,www.other.tld:81;localhost:8081")
    options, args = parser.parse_args()
    setattr(throxy,'options',options)
    setattr(throxy,'args',args)
    throxy.debug("starting proxy")
    proxy = ProxyServer()
    try:
        asyncore.loop(timeout=0.1)
    except KeyboardInterrupt:
        pass
    except:
        proxy.shutdown(2)
        proxy.close()
        raise
    try:
        proxy.shutdown(2)
    except:
        pass
    proxy.close()
    throxy.debug("\nproxy stopped")
