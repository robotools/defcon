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

    ===========================
    Name
    ===========================
    ImageSet.FileNamesChanged
    ImageSet.ImageChanged
    ImageSet.ImageWillBeDeleted
    ImageSet.ImageDeleted
    ===========================

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

    representationFactories = {}

    def __init__(self, fileNames=None):
        super(ImageSet, self).__init__()
        self._data = {}
        self._scheduledForDeletion = {}

    def _get_font(self):
        return self.getParent()

    font = property(_get_font, doc="The :class:`Font` that this object belongs to.")

    def _get_fileNames(self):
        return self._data.keys()

    def _set_fileNames(self, fileNames):
        assert not self._data
        oldValue = self._data.keys()
        for fileName in fileNames:
            self._data[fileName] = _imageDict(onDisk=True)
        self.postNotification("ImageSet.FileNamesChanged", data=dict(oldValue=oldValue, newValue=fileNames))

    fileNames = property(_get_fileNames, _set_fileNames, doc="A list of all image file names. This should not be set externally.")

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
            d["onDisk"] = True
            d["onDiskModTime"] = reader.getFileModificationTime(os.path.join("images", fileName))
        return d["data"]

    def __setitem__(self, fileName, data):
        if fileName not in self._data:
            assert fileName == self.makeFileName(fileName)
        assert data.startswith(pngSignature)
        # preserve exsiting stamping
        onDisk = False
        onDiskModTime = None
        if fileName in self._scheduledForDeletion:
            assert fileName not in self._data
            self._data[fileName] = self._scheduledForDeletion.pop(fileName)
        if fileName in self._data:
            n = self[fileName] # force it to load so that the stamping is correct
            onDisk = self._data[fileName]["onDisk"]
            onDiskModTime = self._data[fileName]["onDiskModTime"]
            del self._data[fileName] # now remove it
        self._data[fileName] = _imageDict(data=data, dirty=True, digest=_makeDigest(data), onDisk=onDisk, onDiskModTime=onDiskModTime)
        self.postNotification("ImageSet.ImageChanged", data=dict(name=fileName))
        self.dirty = True

    def __delitem__(self, fileName):
        n = self[fileName] # force it to load so that the stamping is correct
        self.postNotification("ImageSet.ImageWillBeDeleted", data=dict(name=fileName))
        self._scheduledForDeletion[fileName] = dict(self._data.pop(fileName))
        self.postNotification("ImageSet.ImageDeleted", data=dict(name=fileName))
        self.dirty = True

    # ---------------
    # File Management
    # ---------------

    def getSaveProgressBarTickCount(self, formatVersion):
        """
        Get the number of ticks that will be used by a progress bar
        in the save method. This method should not be called externally.
        Subclasses may override this method to implement custom saving behavior.
        """
        return 0

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
        reader = UFOReader(writer.path)
        for fileName, data in self._data.items():
            if not data["dirty"]:
                continue
            writer.writeImage(fileName, data["data"])
            data["dirty"] = False
            data["onDisk"] = True
            data["onDiskModTime"] = reader.getFileModificationTime(os.path.join("images", fileName))
        self.dirty = False

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

    # ---------------------
    # External Edit Support
    # ---------------------

    def testForExternalChanges(self, reader):
        """
        Test for external changes. This should not be called externally.
        """
        filesOnDisk = reader.getImageDirectoryListing()
        modifiedImages = []
        addedImages = []
        deletedImages = []
        for fileName in set(filesOnDisk) - set(self.fileNames):
            if not fileName in self._scheduledForDeletion:
                addedImages.append(fileName)
            elif not self._scheduledForDeletion[fileName]["onDisk"]:
                addedImages.append(fileName)
            elif self._scheduledForDeletion[fileName]["onDiskModTime"] != reader.getFileModificationTime(os.path.join("images", fileName)):
                addedImages.append(fileName)
        for fileName, imageData in self._data.items():
            # file on disk and has been loaded
            if fileName in filesOnDisk and imageData["data"] is not None:
                newModTime = reader.getFileModificationTime(os.path.join("images", fileName))
                if newModTime != imageData["onDiskModTime"]:
                    newData = reader.readImage(fileName)
                    newDigest = _makeDigest(newData)
                    if newDigest != imageData["digest"]:
                        modifiedImages.append(fileName)
                continue
            # file removed
            if fileName not in filesOnDisk and imageData["onDisk"]:
                deletedImages.append(fileName)
                continue
        return modifiedImages, addedImages, deletedImages

    def reloadImages(self, fileNames):
        """
        Reload specified images. This should not be called externally.
        """
        for fileName in fileNames:
            self._data[fileName] = _imageDict()
            image = self[fileName]


def _imageDict(data=None, dirty=False, digest=None, onDisk=True, onDiskModTime=None):
    return dict(data=data, digest=digest, dirty=dirty, onDisk=onDisk, onDiskModTime=onDiskModTime)

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

def _testExternalChanges():
    """
    >>> from ufoLib import UFOReader
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font

    # remove in memory and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> del font.images["image 1.png"]
    >>> reader = UFOReader(path)
    >>> font.images.testForExternalChanges(reader)
    ([], [], [])
    >>> tearDownTestFontCopy()

    # add in memory and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> font.images["image 3.png"] = pngSignature + "blah"
    >>> reader = UFOReader(path)
    >>> font.images.testForExternalChanges(reader)
    ([], [], [])
    >>> tearDownTestFontCopy()

    # modify in memory and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> font.images["image 1.png"] = pngSignature + "blah"
    >>> reader = UFOReader(path)
    >>> font.images.testForExternalChanges(reader)
    ([], [], [])
    >>> tearDownTestFontCopy()

    # remove on disk and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> image = font.images["image 1.png"]
    >>> os.remove(os.path.join(path, "images", "image 1.png"))
    >>> font.images.testForExternalChanges(reader)
    ([], [], ['image 1.png'])
    >>> tearDownTestFontCopy()

    # add on disk and scan
    >>> import shutil
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> source = os.path.join(path, "images", "image 1.png")
    >>> dest = os.path.join(path, "images", "image 3.png")
    >>> shutil.copy(source, dest)
    >>> font.images.testForExternalChanges(reader)
    ([], ['image 3.png'], [])
    >>> tearDownTestFontCopy()

    # modify on disk and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> image = font.images["image 1.png"]
    >>> imagePath = os.path.join(path, "images", "image 1.png")
    >>> f = open(imagePath, "rb")
    >>> data = f.read()
    >>> f.close()
    >>> f = open(imagePath, "wb")
    >>> f.write(data + "blah")
    >>> f.close()
    >>> font.images.testForExternalChanges(reader)
    (['image 1.png'], [], [])
    >>> tearDownTestFontCopy()
    """

def _testReloadImages():
    """
    >>> from ufoLib import UFOReader
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font

    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> image = font.images["image 1.png"]
    >>> imagePath = os.path.join(path, "images", "image 1.png")
    >>> newImageData = pngSignature + "blah"
    >>> f = open(imagePath, "wb")
    >>> f.write(newImageData)
    >>> f.close()
    >>> font.images.reloadImages(["image 1.png"])
    >>> image = font.images["image 1.png"]
    >>> image == newImageData
    True
    >>> tearDownTestFontCopy()
    """


if __name__ == "__main__":
    import doctest
    doctest.testmod()
