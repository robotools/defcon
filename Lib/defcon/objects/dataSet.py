import os
import weakref
from ufoLib import UFOReader, UFOLibError
from defcon.objects.base import BaseObject

pngSignature = "\x89PNG\r\n\x1a\n"


class DataSet(BaseObject):

    """
    This object manages all contents of the data directory in the font.

    **This object posts the following notifications:**

    ===============
    Name
    ===============
    DataSet.Changed
    ===============

    """

    changeNotificationName = "DataSet.Changed"
    representationFactories = {}

    def __init__(self, font=None):
        self._font = None
        if font is not None:
            self._font = weakref.ref(font)
        super(DataSet, self).__init__()
        self.beginSelfNotificationObservation()
        self._data = {}
        self._scheduledForDeletion = {}

    # --------------
    # Parent Objects
    # --------------

    def getParent(self):
        return self.font

    def _get_font(self):
        if self._font is not None:
            return self._font()
        return None

    font = property(_get_font, doc="The :class:`Font` that this object belongs to.")

    # ----------
    # File Names
    # ----------

    def _get_fileNames(self):
        return list(self._data.keys())

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
            path = self.font.path
            reader = UFOReader(path)
            path = os.path.join("data", fileName)
            data = reader.readBytesFromPath(path)
            onDiskModTime = reader.getFileModificationTime(path)
            self._data[fileName] = _dataDict(data=data, onDisk=True, onDiskModTime=onDiskModTime)
        return self._data[fileName]["data"]

    def __setitem__(self, fileName, data):
        assert data is not None
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
        self._data[fileName] = _dataDict(data=data, dirty=True, onDisk=onDisk, onDiskModTime=onDiskModTime)
        self.dirty = True

    def __delitem__(self, fileName):
        n = self[fileName] # force it to load so that the stamping is correct]
        self._scheduledForDeletion[fileName] = dict(self._data.pop(fileName))
        self.dirty = True

    # ----
    # Save
    # ----

    def getSaveProgressBarTickCount(self, formatVersion):
        """
        Get the number of ticks that will be used by a progress bar
        in the save method. This method should not be called externally.
        Subclasses may override this method to implement custom saving behavior.
        """
        return 0

    def save(self, writer, saveAs=False, progressBar=None):
        """
        Save data. This method should not be called externally.
        Subclasses may override this method to implement custom saving behavior.
        """
        if saveAs:
            font = self.font
            if font is not None and font.path is not None and os.path.exists(font.path):
                reader = UFOReader(font.path)
                readerDataDirectoryListing = reader.getDataDirectoryListing()
                for fileName, data in list(self._data.items()):
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
        reader = UFOReader(writer.path)
        for fileName, data in list(self._data.items()):
            if not data["dirty"]:
                continue
            path = os.path.join("data", fileName)
            writer.writeBytesToPath(path, data["data"])
            data["dirty"] = False
            data["onDisk"] = True
            data["onDiskModTime"] = reader.getFileModificationTime(os.path.join("data", fileName))
        self.dirty = False

    # ---------------------
    # External Edit Support
    # ---------------------

    def testForExternalChanges(self, reader):
        """
        Test for external changes. This should not be called externally.
        """
        filesOnDisk = reader.getDataDirectoryListing()
        modified = []
        added = []
        deleted = []
        for fileName in set(filesOnDisk) - set(self.fileNames):
            if not fileName in self._scheduledForDeletion:
                added.append(fileName)
            elif not self._scheduledForDeletion[fileName]["onDisk"]:
                added.append(fileName)
            elif self._scheduledForDeletion[fileName]["onDiskModTime"] != reader.getFileModificationTime(os.path.join("data", fileName)):
                added.append(fileName)
        for fileName, data in list(self._data.items()):
            # file on disk and has been loaded
            if fileName in filesOnDisk and data["data"] is not None:
                path = os.path.join("data", fileName)
                newModTime = reader.getFileModificationTime(path)
                if newModTime != data["onDiskModTime"]:
                    newData = reader.readBytesFromPath(path)
                    if newData != data["data"]:
                        modified.append(fileName)
                continue
            # file removed
            if fileName not in filesOnDisk and data["onDisk"]:
                deleted.append(fileName)
                continue
        return modified, added, deleted

    def reloadData(self, fileNames):
        """
        Reload specified data. This should not be called externally.
        """
        for fileName in fileNames:
            self._data[fileName] = _dataDict()
            data = self[fileName]

    # ------------------------
    # Notification Observation
    # ------------------------

    def endSelfNotificationObservation(self):
        super(DataSet, self).endSelfNotificationObservation()
        self._font = None

    # -----------------------------
    # Serialization/Deserialization
    # -----------------------------

    def getDataForSerialization(self, **kwargs):
        simple_get = lambda key: self[key]

        getters = []
        for k in self.fileNames:
            getters.append((k, simple_get))

        return self._serialize(getters, **kwargs)

    def setDataFromSerialization(self, data):
        self._data = {}
        self._scheduledForDeletion = {}
        for k in data:
            self[k] = data[k]


def _dataDict(data=None, dirty=False, onDisk=True, onDiskModTime=None):
    return dict(data=data, dirty=dirty, onDisk=onDisk, onDiskModTime=onDiskModTime)


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

def _testExternalChanges():
    """
    >>> from ufoLib import UFOReader
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font

    # remove in memory and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> del font.data["com.typesupply.defcon.test.file"]
    >>> reader = UFOReader(path)
    >>> font.data.testForExternalChanges(reader)
    ([], [], [])
    >>> tearDownTestFontCopy()

    # add in memory and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> font.data["com.typesupply.defcon.test.file2"] = "blah"
    >>> reader = UFOReader(path)
    >>> font.data.testForExternalChanges(reader)
    ([], [], [])
    >>> tearDownTestFontCopy()

    # modify in memory and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> font.data["com.typesupply.defcon.test.file"] = "blah"
    >>> reader = UFOReader(path)
    >>> font.data.testForExternalChanges(reader)
    ([], [], [])
    >>> tearDownTestFontCopy()

    # remove on disk and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> image = font.data["com.typesupply.defcon.test.file"]
    >>> os.remove(os.path.join(path, "data", "com.typesupply.defcon.test.file"))
    >>> font.data.testForExternalChanges(reader)
    ([], [], ['com.typesupply.defcon.test.file'])
    >>> tearDownTestFontCopy()

    # add on disk and scan
    >>> import shutil
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> source = os.path.join(path, "data", "com.typesupply.defcon.test.file")
    >>> dest = os.path.join(path, "data", "com.typesupply.defcon.test.file2")
    >>> shutil.copy(source, dest)
    >>> font.data.testForExternalChanges(reader)
    ([], ['com.typesupply.defcon.test.file2'], [])
    >>> tearDownTestFontCopy()

    # modify on disk and scan
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> d = font.data["com.typesupply.defcon.test.file"]
    >>> filePath = os.path.join(path, "data", "com.typesupply.defcon.test.file")
    >>> f = open(filePath, "wb")
    >>> f.write("blah")
    >>> f.close()
    >>> reader = UFOReader(path)
    >>> font.data.testForExternalChanges(reader)
    (['com.typesupply.defcon.test.file'], [], [])
    >>> tearDownTestFontCopy()
    """

def _testReloadData():
    """
    >>> from ufoLib import UFOReader
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font

    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> d = font.data["com.typesupply.defcon.test.file"]
    >>> filePath = os.path.join(path, "data", "com.typesupply.defcon.test.file")
    >>> newData = "blah"
    >>> f = open(filePath, "wb")
    >>> f.write(newData)
    >>> f.close()
    >>> font.data.reloadData(["com.typesupply.defcon.test.file"])
    >>> data = font.data["com.typesupply.defcon.test.file"]
    >>> data == newData
    True
    >>> tearDownTestFontCopy()
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
