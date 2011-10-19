import os
from ufoLib import UFOReader, UFOLibError
from defcon.objects.base import BaseObject

pngSignature = "\x89PNG\r\n\x1a\n"


class DataSet(BaseObject):

    """
    This object manages all contents of the data directory in the font.

    **This object posts the following notifications:**

    ===========      ====
    Name             Note
    ===========      ====
    DataSet.Changed  Posted when the *dirty* attribute is set.
    ===========      ====

    """

    def __init__(self, fileNames=None):
        super(DataSet, self).__init__()
        self._data = {}
        self._scheduledForDeletion = set()

    def _get_fileNames(self):
        return self._data.keys()

    def _set_fileNames(self, fileNames):
        assert not self._data
        for fileName in fileNames:
            self._data[fileName] = _dataDict()

    fileNames = property(_get_fileNames, _set_fileNames, doc="A list of all file names. This should not be set externally.")

    # -------------
    # Dict Behavior
    # -------------

    def __getitem__(self, fileName):
        if self._data[fileName]["data"] is None:
            path = self.getParent().path
            reader = UFOReader(path)
            path = os.path.join("data", fileName)
            data = reader.readBytesFromPath(path)
            self._data[fileName] = _dataDict(data=data)
        return self._data[fileName]["data"]

    def __setitem__(self, fileName, data):
        assert data is not None
        self._data[fileName] = _dataDict(data=data, dirty=True)
        self._scheduledForDeletion.discard(fileName)
        self.dirty = True

    def __delitem__(self, fileName):
        del self._data[fileName]
        self._scheduledForDeletion.add(fileName)
        self.dirty = True

    # ---------------
    # File Management
    # ---------------

    def save(self, writer, saveAs=False, progressBar=None):
        """
        Save data. This method should not be called externally.
        Subclasses may override this method to implement custom saving behavior.
        """
        if saveAs:
            font = self.getParent()
            if font is not None and font.path is not None and os.path.exists(font.path):
                reader = UFOReader(font.path)
                readerDataDirectoryListing = reader.getDataDirectoryListing()
                for fileName, data in self._data.items():
                    path = os.path.join("data", fileName)
                    if data["data"] is not None or fileName not in readerDataDirectoryListing:
                        continue
                    writer.copyFromReader(reader, path, path)
        for fileName in self._scheduledForDeletion:
            try:
                path = os.path.join("data", fileName)
                writer.removeFileForPath(path)
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
            path = os.path.join("data", fileName)
            writer.writeBytesToPath(path, data["data"])
            data["dirty"] = False
        self.dirty = False


def _dataDict(data=None, dirty=False):
    return dict(data=data, dirty=dirty)


# -----
# Tests
# -----

def _testRead():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> for fileName in sorted(font.data.fileNames):
    ...     if True in [i.startswith(".") for i in fileName.split(os.sep)]:
    ...         continue
    ...     fileName
    'com.typesupply.defcon.test.directory/file 1.txt'
    'com.typesupply.defcon.test.directory/sub directory/file 2.txt'
    'com.typesupply.defcon.test.file'
    >>> font.data["com.typesupply.defcon.test.directory/file 1.txt"]
    'This is file 1.'
    >>> font.data["com.typesupply.defcon.test.directory/sub directory/file 2.txt"]
    'This is file 2.'
    >>> font.data["com.typesupply.defcon.test.file"]
    'This is a top level test file.'
    """

def _testWrite():
    """
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> font.data["com.typesupply.defcon.test.newdirectory/file.txt"] = "hello."
    >>> del font.data["com.typesupply.defcon.test.directory/sub directory/file 2.txt"]
    >>> font.save()
    >>> p = os.path.join(path, "data", "com.typesupply.defcon.test.newdirectory/file.txt")
    >>> os.path.exists(p)
    True
    >>> f = open(p, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t
    'hello.'
    >>> p = os.path.join(path, "data", "com.typesupply.defcon.test.directory/sub directory/file 2.txt")
    >>> os.path.exists(p)
    False
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
    >>> dataDirectory = os.path.join(saveAsPath, "data")
    >>> os.path.exists(dataDirectory)
    True
    >>> os.path.exists(os.path.join(dataDirectory, "com.typesupply.defcon.test.directory/file 1.txt"))
    True
    >>> os.path.exists(os.path.join(dataDirectory, "com.typesupply.defcon.test.directory/sub directory/file 2.txt"))
    True
    >>> os.path.exists(os.path.join(dataDirectory, "com.typesupply.defcon.test.file"))
    True
    >>> tearDownTestFontCopy(saveAsPath)
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
