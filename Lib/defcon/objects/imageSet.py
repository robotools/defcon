import os
import hashlib
from ufoLib import UFOReader, UFOLibError
from defcon.objects.base import BaseObject
from ufoLib.filenames import userNameToFileName

pngSignature = "\x89PNG\r\n\x1a\n"


class ImageSet(BaseObject):

    """
    This object manages all images in the font.

    **This object posts the following notifications:**

    ===========       ====
    Name              Note
    ===========       ====
    ImageSet.Changed  Posted when the *dirty* attribute is set.
    ===========       ====

    This object behaves like a dict. For example, to get the
    raw image data for a particular image::

        image = images["image file name"]

    To add an image, do this::

        images["image file name"] = rawImageData

    When setting an image, the provided file name must be a file
    system legal string. This will be checked by comparing the
    provided file name to the results of :py:meth:`ImageSet.makeFileName`.
    If the two don't match an error will be raised.

    Before setting an image, the :py:meth:`ImageSet.findDuplicateImage`
    method should be called. If a file name is retruend, the new image
    data should not be added. The UFO spec recommends (but doesn't require)
    that duplicate images be avoided. This will help with that.

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
            data = reader.readImage(fileName)
            d["data"] = data
            d["digest"] = _makeDigest(data)
        return d["data"]

    def __setitem__(self, fileName, data):
        assert fileName == self.makeFileName(fileName)
        assert data.startswith(pngSignature)
        self._data[fileName] = _imageDict(data=data, dirty=True, digest=_makeDigest(data))
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
        if saveAs:
            font = self.getParent()
            if font is not None and font.path is not None and os.path.exists(font.path):
                reader = UFOReader(font.path)
                readerImageNames = reader.getImageDirectoryListing()
                for fileName, data in self._data.items():
                    if data["data"] is not None or fileName not in readerImageNames:
                        continue
                    writer.copyImageFromReader(reader, fileName, fileName)
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

    def findDuplicateImage(self, data):
        """
        Search the images to see if an image matching
        **image** already exists. If so, the file name
        for the existing image will be returned.
        """
        digest = _makeDigest(data)
        notYetLoaded = []
        for fileName, image in self._data.items():
            # skip if the image hasn't been loaded
            if image["data"] is None:
                notYetLoaded.append(fileName)
                continue
            otherDigest = image["digest"]
            if otherDigest == digest:
                return fileName
        for fileName in notYetLoaded:
            d = self[fileName]
            image = self._data[fileName]
            otherDigest = image["digest"]
            if otherDigest == digest:
                return fileName
        return None


def _imageDict(data=None, dirty=False, digest=None):
    return dict(data=data, digest=digest, dirty=dirty)

def _makeDigest(data):
    m = hashlib.md5()
    m.update(data)
    return m.digest()

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

def _testSaveAs():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath, getTestFontCopyPath, tearDownTestFontCopy
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> saveAsPath = getTestFontCopyPath(path)
    >>> font.save(saveAsPath)
    >>> imagesDirectory = os.path.join(saveAsPath, "images")
    >>> os.path.exists(imagesDirectory)
    True
    >>> imagePath = os.path.join(imagesDirectory, "image 1.png")
    >>> os.path.exists(imagePath)
    True
    >>> imagePath = os.path.join(imagesDirectory, "image 2.png")
    >>> os.path.exists(imagePath)
    True
    >>> tearDownTestFontCopy(saveAsPath)
    """

def _testUnreferencedImages():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.images.unreferencedFileNames
    ['image 2.png']

    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> font.save(removeUnreferencedImages=True)
    >>> p = os.path.join(path, "images", "image 1.png")
    >>> os.path.exists(p)
    True
    >>> p = os.path.join(path, "images", "image 2.png")
    >>> os.path.exists(p)
    False
    >>> tearDownTestFontCopy()
    """

def _testDuplicateImage():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> data = font.images["image 1.png"]
    >>> font.images.findDuplicateImage(data)
    'image 1.png'
    >>> imagePath = os.path.join(path, "images", "image 2.png")
    >>> f = open(imagePath, "rb")
    >>> data = f.read()
    >>> f.close()
    >>> font.images.findDuplicateImage(data)
    'image 2.png'
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
