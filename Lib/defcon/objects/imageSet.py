import os
from ufoLib import UFOReader, UFOLibError
from defcon.objects.base import BaseObject
from ufoLib.filenames import userNameToFileName

pngSignature = "\x89PNG\r\n\x1a\n"


class ImageSet(BaseObject):

    """
    This object manages all images in the font.

    **This object posts the following notifications:**

    ===========    ====
    Name           Note
    ===========    ====
    ImageSet.Changed Posted when the *dirty* attribute is set.
    ===========    ====

    This object behaves like a dict. For example, to get the
    raw image data for a particular image::

        image = images["image file name"]

    To add an image, do this::

        images["image file name"] = rawImageData

    When setting an image, the provided file name must be a file
    system legal string. This will be checked by comparing the
    provided file name to the results of :py:meth:`ImageSet.makeFileName`.
    If the two don't match an error will be raised.

    To remove an image from this object, and from the UFO during save,
    do this::

        del images["image file name"]
    """

    def __init__(self, fileNames=None):
        super(ImageSet, self).__init__()
        self._data = {}
        self._scheduledForDeletion = set()

    def _get_fileNames(self):
        return self._data.keys()

    def _set_fileNames(self, fileNames):
        assert not self._data
        for fileName in fileNames:
            self._data[fileName] = _imageDict()

    fileNames = property(_get_fileNames, _set_fileNames, doc="A list of all image file names.")

    def _get_unreferencedFileNames(self):
        font = self.getParent()
        if font is None:
            return []
        unreferenced = set(self.fileNames)
        for layer in font.layers:
            unreferenced -= set(layer.imageReferences.keys())
        return list(unreferenced)

    unreferencedFileNames = property(_get_unreferencedFileNames, doc="A list of all file names not referenced by a glyph.")

    # -------------
    # Dict Behavior
    # -------------

    def __getitem__(self, fileName):
        d = self._data[fileName]
        if d["data"] is None:
            path = self.getParent().path
            reader = UFOReader(path)
            d["data"] = reader.readImage(fileName)
        return d["data"]

    def __setitem__(self, fileName, data):
        assert fileName == self.makeFileName(fileName)
        assert data.startswith(pngSignature)
        self._data[fileName] = _imageDict(data=data, dirty=True)
        self._scheduledForDeletion.discard(fileName)

    def __delitem__(self, fileName):
        del self._data[fileName]
        self._scheduledForDeletion.add(fileName)

    # ---------------
    # File Management
    # ---------------

    def save(self, writer, removeUnreferencedImages=False, saveAs=False, progressBar=None):
        """
        Save images. This method should not be called externally.
        Subclasses may override this method to implement custom saving behavior.
        """
        if removeUnreferencedImages:
            self.disableNotifications()
            for fileName in self.unreferencedFileNames:
                del self[fileName]
            self.enableNotifications()
        for fileName in self._scheduledForDeletion:
            try:
                writer.removeImage(fileName)
            except UFOLibError:
                # this will be raised if the file doesn't exist.
                # instead of trying to maintain a list of in UFO
                # vs. in memory, simply fail and move on when
                # something can't be deleted because it isn't
                # in the UFO.
                pass
        self._scheduledForDeletion.clear()
        for fileName, data in self._data.items():
            if not data["dirty"]:
                continue
            writer.writeImage(fileName, data["data"])
            data["dirty"] = False

    def makeFileName(self, fileName):
        """
        Make a file system legal version of **fileName**.
        """
        if not isinstance(fileName, unicode):
            fileName = unicode(fileName)
        suffix = ""
        if fileName.lower().endswith(".png"):
            suffix = fileName[-4:]
            fileName = fileName[:-4]
        existing = set([i.lower() for i in self.fileNames])
        return userNameToFileName(fileName, existing, suffix=suffix)


def _imageDict(data=None, dirty=False):
    return dict(data=data, md5=None, dirty=dirty)

# -----
# Tests
# -----

def _testRead():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> sorted(font.images.fileNames)
    ['image 1.png', 'image 2.png']

    >>> data = font.images["image 1.png"]
    >>> p = os.path.join(path, "images", "image 1.png")
    >>> f = open(p, "rb")
    >>> expected = f.read()
    >>> f.close()
    >>> data == expected
    True

    >>> data = font.images["image 2.png"]
    >>> p = os.path.join(path, "images", "image 2.png")
    >>> f = open(p, "rb")
    >>> expected = f.read()
    >>> f.close()
    >>> data == expected
    True
    """

def _testWrite():
    """
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> font.images["image 3.png"] = font.images["image 1.png"]
    >>> del font.images["image 1.png"]
    >>> font.save()
    >>> p = os.path.join(path, "images", "image 1.png")
    >>> os.path.exists(p)
    False
    >>> p = os.path.join(path, "images", "image 2.png")
    >>> os.path.exists(p)
    True
    >>> p = os.path.join(path, "images", "image 3.png")
    >>> os.path.exists(p)
    True
    >>> tearDownTestFontCopy()
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
