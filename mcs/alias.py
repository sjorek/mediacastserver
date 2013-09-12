# © copyright 2011-2013 Stephan Jorek <stephan.jorek@gmail.com>.
# See LICENSE for details.

def rewrite(aliasPath, destPath):
    """
    Original implementation in twisted.web.rewrite.alias.  This one
    supports an empty alias destination.

    I am not a very good aliaser. But I'm the best I can be. If I'm
    aliasing to a Resource that generates links, and it uses any parts
    of request.prepath to do so, the links will not be relative to the
    aliased path, but rather to the aliased-to path. That I can't
    alias static.File directory listings that nicely. However, I can
    still be useful, as many resources will play nice.
    """
    aliasPath = aliasPath.split('/')
    destPath = destPath.split('/')
    if destPath == ['']:
        def prepend_destPath(after):
            return after or ['']
    else:
        def prepend_destPath(after):
            return destPath + after
    def rewriter(request):
        if request.postpath[:len(aliasPath)] == aliasPath:
            after = request.postpath[len(aliasPath):]
            request.postpath = prepend_destPath(after)
            request.path = '/' + '/'.join(request.prepath + request.postpath)
    return rewriter