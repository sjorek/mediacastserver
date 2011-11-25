# Copyright (c) 2011 Stephan Jorek <stephan.jorek@gmail.com>.
# See LICENSE for details.

from twisted.application.service import ServiceMaker

TwistedMCS = ServiceMaker(
    "HTTP Server for static files",
    "mcs.server",
    "A general-purpose web server, intended to serve from a filesystem.",
    "mediacastserver")
