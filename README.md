Mediacast Server
================

Version 0.0.1

This project provides a webserver for static content with support for
virtual-hosts, path-aliases, per-host/-ip traffic-shaping capabilities,
reverse-proxing with internal url-translation and multicast-DNS (bonjour)
service-advertisement written in Python.


Why another webserver ?
-----------------------

The main purpose of this webserver is bandwidth-limiting, utilizing the
[token-bucket algorithm](http://en.wikipedia.org/wiki/Token_bucket).  The
server is therefore ideal to be used in multimedia-production toolchains, in
order to verify http-video- and audio-streaming bandwidth-usage and browser
behavior in this context. Currently it serves any static file content, like
those produced by [Apple's “mediastreamsegmenter”](http://developer.apple.com/library/mac/#documentation/Darwin/Reference/ManPages/man1/mediastreamsegmenter.1.html)
or f4f-streams as specified by Adobe in the [f4f file format specification](http://www.adobe.com/products/httpdynamicstreaming/).

The implementation is based upon the fantastic Twisted-Framework and is
implemented as a plugin therein.

As Twisted supports integration into the Win32, Mac OSX and of course Linux
operating systems, the server may work in these environments in future
releases.  Currently only Mac OSX 10.6.x are tested and supported.  Apple's
default python-installation and twisted-package is sufficient in order to run
the webserver.  That also means that at this time only python 2.6 is verified.


Installation
------------

Instructions for installing this software are in [INSTALL](INSTALL.md).


Usage
-----


Execute `PYTHONPATH=path/to/mediacastserver twistd mediacastserver --help` to
get a detailed command usage reference.  If you do so you should get something
like:

    Usage: twistd [options] mediacastserver [mediacastserver options]
    Options:
    -n, --notracebacks      Display tracebacks in broken web pages. Displaying
                          tracebacks to users may be security risk!
    -l, --logfile=          Path to web CLF (Combined Log Format) log file.
      --help              Display this help and exit.
    -s, --shape=            Limit download bandwidth server-wide, optionally with
                          server-wide initial burst, per client-connection
                          rate-limit and per client-connection initial burst:
                          server-wide-rate[,per-client-rate[,server-wide-burst[,per-client-burst]]]
      --ignore-ext=       Specify an extension to ignore. These will be
                          processed in order.
    -p, --port=             strports description of the port to start the server
                          on.
    -i, --index=            Add the name of a file used to check for directory
                          indexes. [default: index, index.html]
    -a, --alias=            Alias(es) mapping a (virtual) path to a (real) path,
                          eg.: alias/path[,real/path]
      --version
      --mime-type=        Specify the default mime-type for static files.
      --monster=          add a vhost monster child-path intended to connect a reverse proxy.

                          This makes it possible to put it behind a reverse proxy transparently. Just have
                          the reverse proxy proxy to

                          host,port,/vhost-monster-child-path/http/external-host:port/

                          and on redirects and other link calculation, the external-host:port will be
                          transmitted to this client.

    -v, --vhost=            Additional vhost(s) to run, eg.: host.domain.tld
    -h, --host=             port number (not strports description!) to start an
                          additional server on.
    -u, --user              Makes a server with ~/public_html and ~/.twistd-web-pb
                          support for users.
      --allow-ignore-ext  Specify whether or not a request for 'foo' should
                          return 'foo.ext'
      --path=             <path> is either a specific file or a directory to be
                          set as the root of the web server.
      --bonjour=          override or append additional bonjour (mDNS/zeroconf)
                          record. the first occurrence per host overrides the
                          default description, subsequent occurrences append
                          additional records. eg.: 'computer %s on port %d'
      --reverse=          run a reverse proxy, either as the whole server or on
                          a direct child-path (leaf) only eg.:
                          host.domain.tld[,port-number[,path/to/proxy[,path/on/this/server]]]


Documentation and Support
------------------------


Sorry, but you have to use the force and read the source. Help might also be
available on the [Twisted mailing list](http://twistedmatrix.com/cgi-bin/mailman/listinfo/twisted-python)
If you need more inspiration, feel free to contact me.


TODOs
-----


* Write a setup.py
* Write unit-tests (a shame that it's not yet done, i know)
* Get rid of the Apple-specific bonjour and hostname implementation, test and
support Avahi-Daemon
* Make mDNS-support optional anyway, as it creates an additional dependency
to pybonjour-package
* Test and support Win32-environments

Copyright
---------


All of the code in this distribution is © copyright 2011-2017 Stephan Jorek.

The included [LICENSE](LICENSE) file describes this in detail.
Twisted itself is made available under the MIT license. 

Warranty
--------

THIS SOFTWARE IS PROVIDED "AS IS" WITHOUT WARRANTY OF ANY KIND, EITHER
EXPRESSED OR IMPLIED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE.  THE ENTIRE RISK AS
TO THE USE OF THIS SOFTWARE IS WITH YOU.

IN NO EVENT WILL ANY COPYRIGHT HOLDER, OR ANY OTHER PARTY WHO MAY MODIFY
AND/OR REDISTRIBUTE THE LIBRARY, BE LIABLE TO YOU FOR ANY DAMAGES, EVEN IF
SUCH HOLDER OR OTHER PARTY HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH
DAMAGES.

Again, see the included [LICENSE](LICENSE) file for specific legal details.
