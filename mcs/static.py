from twisted.web import static
from mcs import mediatypes

class File(static.File):
    __doc__ = static.File.__doc__
    
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

