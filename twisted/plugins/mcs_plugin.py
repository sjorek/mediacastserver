# Copyright (c) 2001-2008 Twisted Matrix Laboratories.
# See LICENSE for details.

from twisted.application.service import ServiceMaker

TwistedHSS = ServiceMaker(
    "HTTP(s) Server for static files",
    "mcs.server",
    "A general-purpose web server which serves from a filesystem.",
    "mediacastserver")
