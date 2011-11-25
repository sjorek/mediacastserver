# Copyright (c) 2011 Stephan Jorek <stephan.jorek@gmail.com>.
# See LICENSE for details.

from twisted.web import static

from mcs import mediatypes

Data = static.Data

class PathSegment(static.Data):
    def __init__(self):
        static.Data.__init__(self, type='text/html', data='')

class File(static.File):

    contentTypes = static.File.contentTypes
    contentTypes.update(mediatypes.VIDEO_MIME_TYPES)

    def __init__(self, path, defaultType=mediatypes.DEFAULT_MIME_TYPE,
                 ignoredExts=(), registry=None, allowExt=0):
        """Create a file with the given path.
        """
        static.File.__init__(self, path=path, defaultType=defaultType,
                             ignoredExts=ignoredExts, registry=registry,
                             allowExt=allowExt)

    def upgradeToVersion2(self):
        self.defaultType = mediatypes.DEFAULT_MIME_TYPE

