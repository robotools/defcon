import os
import weakref
from robofab.ufoLib import UFOReader, UFOWriter
from defcon.objects.base import BaseObject
from defcon.objects.glyph import Glyph
from defcon.objects.info import Info
from defcon.objects.kerning import Kerning
from defcon.objects.groups import Groups
from defcon.objects.lib import Lib
from defcon.tools.notifications import NotificationCenter


class Font(BaseObject):

    _notificationName = "Font.Changed"

    def __init__(self, path=None,
                    kerningClass=None, infoClass=None, groupsClass=None, libClass=None,
                    glyphClass=None, glyphContourClass=None):
        super(Font, self).__init__()
        if glyphClass is None:
            glyphClass = Glyph
        if infoClass is None:
            infoClass = Info
        if kerningClass is None:
            kerningClass = Kerning
        if groupsClass is None:
            groupsClass = Groups
        if libClass is None:
            libClass = Lib

        self._dispatcher = NotificationCenter()

        self._glyphClass = glyphClass
        self._glyphContourClass = glyphContourClass

        self._kerningClass = kerningClass
        self._infoClass = infoClass
        self._groupsClass = groupsClass
        self._libClass = libClass

        self._path = path

        self._glyphs = {}
        self._glyphSet = None
        self._scheduledForDeletion = []
        self._keys = set()

        self._kerning = None
        self._info = None
        self._groups = None
        self._lib = None
        self.cmap = {}

        self._dirty = False

        if path:
            r = UFOReader(self._path)
            self._glyphSet = r.getGlyphSet()
            self.cmap = r.getCharacterMapping()
            self._keys = set(self._glyphSet.keys())

    def _loadGlyph(self, name):
        if self._glyphSet is None or not self._glyphSet.has_key(name):
            raise KeyError, '%s not in font' % name
        glyph = self._glyphClass(dispatcher=self.dispatcher, contourClass=self._glyphContourClass)
        pointPen = glyph.getPointPen()
        self._glyphSet.readGlyph(glyphName=name, glyphObject=glyph, pointPen=pointPen)
        glyph.dirty = False
        self._glyphs[name] = glyph
        self._setParentDataInGlyph(glyph)
        self._stampGlyphDataState(glyph)
        return glyph

    def _setParentDataInGlyph(self, glyph):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> id(glyph.getParent()) == id(font)
        True
        """
        glyph.setParent(self)
        glyph.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Glyph.Changed")
        glyph.addObserver(observer=self, methodName="_glyphNameChange", notification="Glyph.NameChanged")
        glyph.addObserver(observer=self, methodName="_glyphUnicodesChange", notification="Glyph.UnicodesChanged")

    def newGlyph(self, name):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> font.newGlyph('NewGlyphTest')
        >>> glyph = font['NewGlyphTest']
        >>> glyph.name
        'NewGlyphTest'
        >>> glyph.dirty
        True
        >>> font.dirty
        True
        >>> keys = font.keys()
        >>> keys.sort()
        >>> keys
        ['A', 'B', 'C', 'NewGlyphTest']
        """
        if name in self:
            self._removeFromCMAP(name)
        glyph = self._glyphClass(self.dispatcher, contourClass=self._glyphContourClass)
        glyph.name = name
        self._glyphs[name] = glyph
        self._setParentDataInGlyph(glyph)
        self.dirty = True
        # a glyph by the same name could be
        # scheduled for deletion
        if name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(name)
        # keep the keys up to date
        self._keys.add(name)

    def insertGlyph(self, glyph, name=None):
        """
        >>> "need insert glyph test!"
        """
        from copy import deepcopy
        source = glyph
        if name is None:
            name = source.name
        self.newGlyph(name)
        dest = self[name]
        pointPen = dest.getPointPen()
        source.drawPoints(pointPen)
        dest.width = source.width
        dest.unicodes = list(source.unicodes)
        dest.note = source.note
        dest.lib = deepcopy(source.lib)
        if dest.unicodes:
            self._addToCMAP(dest)
        return dest

    def __iter__(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> names = [glyph.name for glyph in font]
        >>> names.sort()
        >>> names
        ['A', 'B', 'C']
        >>> names = []
        >>> for glyph1 in font:
        ...     for glyph2 in font:
        ...         names.append((glyph1.name, glyph2.name))
        >>> names.sort()
        >>> names
        [('A', 'A'), ('A', 'B'), ('A', 'C'), ('B', 'A'), ('B', 'B'), ('B', 'C'), ('C', 'A'), ('C', 'B'), ('C', 'C')]
        """
        names = self.keys()
        while names:
            name = names[0]
            yield self[name]
            names = names[1:]

    def __getitem__(self, name):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> font['A'].name
        'A'
        >>> font['B'].name
        'B'
        >>> font['NotInFont']
        Traceback (most recent call last):
            ...
        KeyError: 'NotInFont not in font'
        """
        if name not in self._glyphs:
            self._loadGlyph(name)
        return self._glyphs[name]

    def __delitem__(self, name):
        """
        >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
        >>> import glob
        >>> import os
        >>> path = makeTestFontCopy()
        >>> font = Font(path)
        >>> del font['A']
        >>> font.dirty
        True
        >>> font.newGlyph('NewGlyphTest')
        >>> del font['NewGlyphTest']
        >>> keys = font.keys()
        >>> keys.sort()
        >>> keys
        ['B', 'C']
        >>> len(font)
        2
        >>> 'A' in font
        False
        >>> font.save()
        >>> fileNames = glob.glob(os.path.join(path, 'Glyphs', '*.glif'))
        >>> fileNames = [os.path.basename(fileName) for fileName in fileNames]
        >>> fileNames.sort()
        >>> fileNames
        ['B_.glif', 'C_.glif']
        >>> del font['NotInFont']
        Traceback (most recent call last):
            ...
        KeyError: 'NotInFont not in font'
        >>> tearDownTestFontCopy()

        # test saving externally deleted glyphs.
        # del glyph. not dirty.
        >>> path = makeTestFontCopy()
        >>> font = Font(path)
        >>> glyph = font["A"]
        >>> glyphPath = os.path.join(path, "glyphs", "A_.glif")
        >>> os.remove(glyphPath)
        >>> r = font.testForExternalChanges()
        >>> r["deletedGlyphs"]
        ['A']
        >>> del font["A"]
        >>> font.save()
        >>> os.path.exists(glyphPath)
        False
        >>> tearDownTestFontCopy()

        # del glyph. dirty.
        >>> path = makeTestFontCopy()
        >>> font = Font(path)
        >>> glyph = font["A"]
        >>> glyph.dirty = True
        >>> glyphPath = os.path.join(path, "glyphs", "A_.glif")
        >>> os.remove(glyphPath)
        >>> r = font.testForExternalChanges()
        >>> r["deletedGlyphs"]
        ['A']
        >>> del font["A"]
        >>> font.save()
        >>> os.path.exists(glyphPath)
        False
        >>> tearDownTestFontCopy()
        """
        if name not in self:
            raise KeyError, '%s not in font' % name
        if name in self._glyphs:
            del self._glyphs[name]
        if name in self._keys:
            self._keys.remove(name)
        self._removeFromCMAP(name)
        if self._glyphSet is not None and name in self._glyphSet:
            self._scheduledForDeletion.append(name)
        self.dirty = True

    def __len__(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> len(font)
        3
        
        >>> font = Font()
        >>> len(font)
        0
        """
        return len(self.keys())

    def __contains__(self, name):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> 'A' in font
        True
        >>> 'NotInFont' in font
        False
        
        >>> font = Font()
        >>> 'A' in font
        False
        """
        return name in self._keys

    def keys(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> keys = font.keys()
        >>> keys.sort()
        >>> print keys
        ['A', 'B', 'C']
        >>> del font["A"]
        >>> keys = font.keys()
        >>> keys.sort()
        >>> print keys
        ['B', 'C']
        >>> font.newGlyph("A")
        >>> keys = font.keys()
        >>> keys.sort()
        >>> print keys
        ['A', 'B', 'C']

        >>> font = Font()
        >>> font.keys()
        []
        >>> font.newGlyph("A")
        >>> keys = font.keys()
        >>> keys.sort()
        >>> print keys
        ['A']
        """
        # this is not generated dynamically since we
        # support external editing. it must be fixed.
        names = self._keys
        names = names - set(self._scheduledForDeletion)
        return list(names)

    # ---------------
    # CMAP management
    # ---------------

    def _removeFromCMAP(self, name):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> font.newGlyph("A")
        >>> font.cmap.get(65)

        >>> font = Font(getTestFontPath())
        >>> font.newGlyph("test")
        >>> glyph = font["test"]
        >>> glyph.unicodes = [65]
        >>> del font["A"]
        >>> font.cmap.get(65)
        ['test']
        """
        reversedCMAP = self.reversedCMAP
        if name in reversedCMAP:
            unicodes = reversedCMAP[name]
            for value in unicodes:
                self.cmap[value].remove(name)
                if not self.cmap[value]:
                    del self.cmap[value]
        self.dispatcher.postNotification(notification="CMAP.Changed", observable=self)

    def _addToCMAP(self, glyph):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> font.newGlyph("test")
        >>> glyph = font["test"]
        >>> glyph.unicodes = [123]
        >>> font.cmap.get(123)
        ['test']
        """
        for value in glyph.unicodes:
            if value not in self.cmap:
                self.cmap[value] = []
            self.cmap[value].append(glyph.name)
        self.dispatcher.postNotification(notification="CMAP.Changed", observable=self)

    # ----------
    # Attributes
    # ----------

    def _get_path(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> path = getTestFontPath()
        >>> font = Font(path)
        >>> font.path == path
        True

        >>> font = Font()
        >>> font.path == None
        True
        """
        return self._path

    path = property(_get_path)

    def _get_reversedCMAP(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> font.reversedCMAP
        {'A': [65], 'C': [67], 'B': [66]}
        >>> font['A'].unicodes = [123, 456]
        >>> font.reversedCMAP
        {'A': [123, 456], 'C': [67], 'B': [66]}
        """
        map = {}
        for univalue, nameList in self.cmap.items():
            for name in nameList:
                if name not in map:
                    map[name] = []
                map[name].append(univalue)
        return map

    reversedCMAP = property(_get_reversedCMAP)

    def _get_glyphsWithOutlines(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> sorted(font.glyphsWithOutlines)
        ['A', 'B']
        >>> font = Font(getTestFontPath())
        >>> for glyph in font:
        ...    pass
        >>> sorted(font.glyphsWithOutlines)
        ['A', 'B']
        """
        import re
        import os
        pointRE = re.compile(
            "<\s*point\s+" # <point
            "[^>]+"        # anything except >
            ">"            # >
        )
        found = []
        # scan loaded glyphs
        for glyphName, glyph in self._glyphs.items():
            if glyphName in self._scheduledForDeletion:
                continue
            if len(glyph):
                found.append(glyphName)
        # scan glyphs that have not been loaded
        glyphsPath = os.path.join(self.path, "glyphs")
        for glyphName, fileName in self._glyphSet.contents.items():
            if glyphName in self._glyphs or glyphName in self._scheduledForDeletion:
                continue
            glyphPath = os.path.join(glyphsPath, fileName)
            f = open(glyphPath, "rb")
            data = f.read()
            f.close()
            containsPoints = False
            # use an re to extract all points
            points = pointRE.findall(data)
            # skip all moves, as individual moves
            # are anchors and therefore not part
            # of an outline.
            for point in points:
                if 'type="move"' not in point:
                    containsPoints = True
                    break
            if containsPoints:
                found.append(glyphName)
        return found

    glyphsWithOutlines = property(_get_glyphsWithOutlines)

    # -----------
    # Sub-Objects
    # -----------

    def _get_info(self):
        if self._info is None:
            self._info = self._infoClass()
            self._info.dispatcher = self.dispatcher
            self._info.setParent(self)
            if self._path is not None:
                u = UFOReader(self._path)
                u.readInfo(self._info)
            self._info.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Info.Changed")
            self._stampInfoDataState()
        return self._info

    info = property(_get_info)

    def _get_kerning(self):
        if self._kerning is None:
            self._kerning = self._kerningClass()
            self._kerning.dispatcher = self.dispatcher
            self._kerning.setParent(self)
            if self._path is not None:
                r = UFOReader(self._path)
                d = r.readKerning()
                self._kerning.update(d)
            self._kerning.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Kerning.Changed")
            self._stampKerningDataState()
        return self._kerning

    kerning = property(_get_kerning)

    def _get_groups(self):
        if self._groups is None:
            self._groups = self._groupsClass()
            self._groups.dispatcher = self.dispatcher
            self._groups.setParent(self)
            if self._path is not None:
                r = UFOReader(self._path)
                d = r.readGroups()
                self._groups.update(d)
            self._groups.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Groups.Changed")
            self._stampGroupsDataState()
        return self._groups

    groups = property(_get_groups)

    def _get_lib(self):
        if self._lib is None:
            self._lib = self._libClass()
            self._lib.dispatcher = self.dispatcher
            self._lib.setParent(self)
            if self._path is not None:
                r = UFOReader(self._path)
                d = r.readLib()
                self._lib.update(d)
            self._stampLibDataState()
        return self._lib

    lib = property(_get_lib)

    # -------
    # Methods
    # -------

    def save(self, path=None):
        """
        >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy, getTestFontPath, getTestFontCopyPath
        >>> import glob
        >>> import os
        >>> path = makeTestFontCopy()
        >>> font = Font(path)
        >>> for glyph in font:
        ...     glyph.dirty = True
        >>> font.save()
        >>> fileNames = glob.glob(os.path.join(path, 'Glyphs', '*.glif'))
        >>> fileNames = [os.path.basename(fileName) for fileName in fileNames]
        >>> fileNames.sort()
        >>> fileNames
        ['A_.glif', 'B_.glif', 'C_.glif']
        >>> tearDownTestFontCopy()

        >>> path = getTestFontPath()
        >>> font = Font(path)
        >>> saveAsPath = getTestFontCopyPath(path)
        >>> font.save(saveAsPath)
        >>> fileNames = glob.glob(os.path.join(saveAsPath, 'Glyphs', '*.glif'))
        >>> fileNames = [os.path.basename(fileName) for fileName in fileNames]
        >>> fileNames.sort()
        >>> fileNames
        ['A_.glif', 'B_.glif', 'C_.glif']
        >>> font.path == saveAsPath
        True
        >>> tearDownTestFontCopy(saveAsPath)
        """
        saveAs = False
        if path is not None and path != self._path:
            saveAs = True
        else:
            path = self._path
        ## make a UFOWriter
        ufoWriter = UFOWriter(path)
        ## save objects
        saveInfo = False
        saveKerning = False
        saveGroups = False
        saveLib = False
        # if in a save as, save all objects
        if saveAs:
            saveInfo = True
            saveKerning = True
            saveGroups = True
            saveLib = True
        # save info and kerning if they are dirty
        if self._info is not None and self._info.dirty:
            saveInfo = True
        if self._kerning is not None and self._kerning.dirty:
            saveKerning = True
        # always save groups and lib if they are loaded
        if self._groups is not None:
            saveGroups = True
        if self._lib is not None:
            saveLib = True
        # save objects as needed
        if saveInfo:
            ufoWriter.writeInfo(self.info)
            self._stampInfoDataState()
            self.info.dirty = False
        if saveKerning:
            ufoWriter.writeKerning(self.kerning)
            self._stampKerningDataState()
            self.kerning.dirty = False
        if saveGroups:
            ufoWriter.writeGroups(self.groups)
            self._stampGroupsDataState()
        if saveLib:
            ufoWriter.writeLib(self.lib)
            self._stampLibDataState()
        ## save glyphs
        # for a save as operation, load all the glyphs
        # and mark them as dirty.
        if saveAs:
            for glyph in self:
                glyph.dirty = True
        glyphSet = ufoWriter.getGlyphSet()
        for glyphName, glyphObject in self._glyphs.items():
            if glyphObject.dirty:
                glyphSet.writeGlyph(glyphName, glyphObject, glyphObject.drawPoints)
                self._stampGlyphDataState(glyphObject)
        # remove deleted glyphs
        if not saveAs and self._scheduledForDeletion:
            for glyphName in self._scheduledForDeletion:
                if glyphName in glyphSet:
                    glyphSet.deleteGlyph(glyphName)
        glyphSet.writeContents()
        self._glyphSet = glyphSet
        self._scheduledForDeletion = []
        self._path = path
        self.dirty = False

    # ----------------------
    # Notification Callbacks
    # ----------------------

    def _objectDirtyStateChange(self, notification):
        if notification.object.dirty:
            self.dirty = True

    def _glyphNameChange(self, notification):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.name = 'NameChangeTest'
        >>> keys = font.keys()
        >>> keys.sort()
        >>> keys
        ['B', 'C', 'NameChangeTest']
        >>> font.dirty
        True
        """
        oldName, newName = notification.data
        glyph = self._glyphs[oldName]
        del self[oldName]
        self._glyphs[newName] = glyph
        self._keys.add(newName)

    def _glyphUnicodesChange(self, notification):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.unicodes = [123, 456]
        >>> font.cmap[123]
        ['A']
        >>> font.cmap[456]
        ['A']
        >>> font.cmap[66]
        ['B']
        >>> font.cmap.get(65)

        >>> font = Font(getTestFontPath())
        >>> font.newGlyph("test")
        >>> glyph = font["test"]
        >>> glyph.unicodes = [65]
        >>> font.cmap[65]
        ['A', 'test']
        """
        glyphName = notification.object.name
        self._removeFromCMAP(glyphName)
        self._addToCMAP(self[glyphName])

    # ---------------------
    # External Edit Support
    # ---------------------

    # data stamping

    def _stampFontDataState(self, obj, fileName):
        # font is not on disk
        if self._path is None:
            return
        # data has not been loaded
        if obj is None:
            return
        path = os.path.join(self._path, fileName)
        # file is not in UFO
        if not os.path.exists(path):
            return
        # get the text
        f = open(path, "rb")
        text = f.read()
        f.close()
        # get the file modification time
        modTime = os.stat(path).st_mtime
        # store the data
        obj._dataOnDisk = text
        obj._dataOnDiskTimeStamp = modTime

    def _stampInfoDataState(self):
        self._stampFontDataState(self._info, "fontinfo.plist")

    def _stampKerningDataState(self):
        self._stampFontDataState(self._kerning, "kerning.plist")

    def _stampGroupsDataState(self):
        self._stampFontDataState(self._groups, "groups.plist")

    def _stampLibDataState(self):
        self._stampFontDataState(self._lib, "lib.plist")

    def _stampGlyphDataState(self, glyph):
        if self._glyphSet is None:
            return
        glyphSet = self._glyphSet
        glyphName = glyph.name
        if glyphName not in glyphSet.contents:
            return
        path = os.path.join(self.path, "glyphs", glyphSet.contents[glyphName])
        # get the text
        f = open(path, "rb")
        text = f.read()
        f.close()
        # get the file modification time
        modTime = os.stat(path).st_mtime
        # store the data
        glyph._dataOnDisk = text
        glyph._dataOnDiskTimeStamp = modTime

    # data comparison

    def testForExternalChanges(self):
        """
        >>> from plistlib import readPlist, writePlist
        >>> from defcon.test.testTools import getTestFontPath
        >>> path = getTestFontPath("TestExternalEditing.ufo")
        >>> font = Font(path)

        # load all the objects so that they get stamped
        >>> i = font.info
        >>> k = font.kerning
        >>> g = font.groups
        >>> l = font.lib
        >>> g = font["A"]

        >>> d = font.testForExternalChanges()
        >>> d["info"]
        False
        >>> d["kerning"]
        False
        >>> d["groups"]
        False
        >>> d["lib"]
        False
        >>> d["modifiedGlyphs"]
        []
        >>> d["addedGlyphs"]
        []
        >>> d["deletedGlyphs"]
        []

        # make a simple change to the kerning data
        >>> path = os.path.join(font.path, "kerning.plist")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t += " "
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        >>> os.utime(path, (k._dataOnDiskTimeStamp + 1, k._dataOnDiskTimeStamp + 1))

        >>> d = font.testForExternalChanges()
        >>> d["kerning"]
        True
        >>> d["info"]
        False

        # save the kerning data and test again
        >>> font.kerning.dirty = True
        >>> font.save()
        >>> d = font.testForExternalChanges()
        >>> d["kerning"]
        False

        # make a simple change to a glyph
        >>> path = os.path.join(font.path, "glyphs", "A_.glif")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t += " "
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        >>> os.utime(path, (g._dataOnDiskTimeStamp + 1, g._dataOnDiskTimeStamp + 1))
        >>> d = font.testForExternalChanges()
        >>> d["modifiedGlyphs"]
        ['A']

        # save the glyph and test again
        >>> font["A"].dirty = True
        >>> font.save()
        >>> d = font.testForExternalChanges()
        >>> d["modifiedGlyphs"]
        []

        # add a glyph
        >>> path = os.path.join(font.path, "glyphs", "A_.glif")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t = t.replace('<glyph name="A" format="1">', '<glyph name="XXX" format="1">')
        >>> path = os.path.join(font.path, "glyphs", "XXX.glif")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        >>> path = os.path.join(font.path, "glyphs", "contents.plist")
        >>> plist = readPlist(path)
        >>> savePlist = dict(plist)
        >>> plist["XXX"] = "XXX.glif"
        >>> writePlist(plist, path)
        >>> d = font.testForExternalChanges()
        >>> d["modifiedGlyphs"]
        []
        >>> d["addedGlyphs"]
        [u'XXX']

        # delete a glyph
        >>> path = getTestFontPath("TestExternalEditing.ufo")
        >>> font = Font(path)
        >>> g = font["XXX"]
        >>> path = os.path.join(font.path, "glyphs", "contents.plist")
        >>> writePlist(savePlist, path)
        >>> path = os.path.join(font.path, "glyphs", "XXX.glif")
        >>> os.remove(path)
        >>> d = font.testForExternalChanges()
        >>> d["modifiedGlyphs"]
        []
        >>> d["deletedGlyphs"]
        ['XXX']
        """
        infoChanged = self._testInfoForExternalModifications()
        kerningChanged = self._testKerningForExternalModifications()
        groupsChanged = self._testGroupsForExternalModifications()
        libChanged = self._testLibForExternalModifications()
        modifiedGlyphs, addedGlyphs, deletedGlyphs = self._testGlyphsForExternalModifications()
        return dict(
            info=infoChanged,
            kerning=kerningChanged,
            groups=groupsChanged,
            lib=libChanged,
            modifiedGlyphs=modifiedGlyphs,
            addedGlyphs=addedGlyphs,
            deletedGlyphs=deletedGlyphs
        )

    def _testFontDataForExternalModifications(self, obj, fileName):
        # font is not on disk
        if self._path is None:
            return False
        # data has not been loaded
        if obj is None:
            return False
        path = os.path.join(self._path, fileName)
        # file is not in UFO
        if not os.path.exists(path):
            return False
        # mod time mismatch
        modTime = os.stat(path).st_mtime
        if obj._dataOnDiskTimeStamp != modTime:
            f = open(path, "rb")
            text = f.read()
            f.close()
            # text mismatch
            if text != obj._dataOnDisk:
                return True
        return False

    def _testInfoForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._info, "fontinfo.plist")

    def _testKerningForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._kerning, "kerning.plist")

    def _testGroupsForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._groups, "groups.plist")

    def _testLibForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._lib, "lib.plist")

    def _testGlyphsForExternalModifications(self):
        # font is not stored on disk
        if self._glyphSet is None:
            return [], [], []
        glyphSet = self._glyphSet
        glyphSet.rebuildContents()
        # glyphs added since we started up
        addedGlyphs = list(set(self._glyphSet.keys()) - self._keys)
        # glyphs deleted since we started up
        deletedGlyphs = list(self._keys - set(self._glyphSet.keys()))
        # glyphs modified since loading
        modifiedGlyphs = []
        for glyphName, glyph in self._glyphs.items():
            # deleted glyph. skip.
            if glyphName not in glyphSet.contents:
                continue
            path = os.path.join(self.path, "glyphs", glyphSet.contents[glyphName])
            modTime = os.stat(path).st_mtime
            # mod time mismatch
            if modTime != glyph._dataOnDiskTimeStamp:
                f = open(path, "rb")
                text = f.read()
                f.close()
                # data mismatch
                if text != glyph._dataOnDisk:
                    modifiedGlyphs.append(glyphName)
        return modifiedGlyphs, addedGlyphs, deletedGlyphs

    # data reloading

    def reloadInfo(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> path = getTestFontPath("TestExternalEditing.ufo")
        >>> font = Font(path)
        >>> info = font.info

        >>> path = os.path.join(font.path, "fontinfo.plist")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t = t.replace("<integer>750</integer>", "<integer>751</integer>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()

        >>> info.ascender
        750
        >>> font.reloadInfo()
        >>> info.ascender
        751

        >>> t = t.replace("<integer>751</integer>", "<integer>750</integer>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        """
        if self._info is None:
            obj = self.info
        else:
            r = UFOReader(self._path)
            newInfo = Info()
            r.readInfo(newInfo)
            oldInfo = self._info
            for attr in dir(newInfo):
                if attr.startswith("_"):
                    continue
                if attr == "dirty":
                    continue
                if attr == "dispatcher":
                    continue
                if not hasattr(oldInfo, attr):
                    continue
                newValue = getattr(newInfo, attr)
                oldValue = getattr(oldInfo, attr)
                if hasattr(newValue, "im_func"):
                    continue
                if oldValue == newValue:
                    continue
                setattr(oldInfo, attr, newValue)
            self._stampInfoDataState()

    def reloadKerning(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> path = getTestFontPath("TestExternalEditing.ufo")
        >>> font = Font(path)
        >>> kerning = font.kerning

        >>> path = os.path.join(font.path, "kerning.plist")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t = t.replace("<integer>-100</integer>", "<integer>-101</integer>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()

        >>> kerning.items()
        [(('A', 'A'), -100)]
        >>> font.reloadKerning()
        >>> kerning.items()
        [(('A', 'A'), -101)]

        >>> t = t.replace("<integer>-101</integer>", "<integer>-100</integer>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        """
        if self._kerning is None:
            obj = self.kerning
        else:
            r = UFOReader(self._path)
            d = r.readKerning()
            self._kerning.clear()
            self._kerning.update(d)
            self._stampKerningDataState()

    def reloadGroups(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> path = getTestFontPath("TestExternalEditing.ufo")
        >>> font = Font(path)
        >>> groups = font.groups

        >>> path = os.path.join(font.path, "groups.plist")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t = t.replace("<key>TestGroup</key>", "<key>XXX</key>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()

        >>> groups.keys()
        ['TestGroup']
        >>> font.reloadGroups()
        >>> groups.keys()
        ['XXX']

        >>> t = t.replace("<key>XXX</key>", "<key>TestGroup</key>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        """
        if self._groups is None:
            obj = self.groups
        else:
            r = UFOReader(self._path)
            d = r.readGroups()
            self._groups.clear()
            self._groups.update(d)
            self._stampGroupsDataState()

    def reloadLib(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> path = getTestFontPath("TestExternalEditing.ufo")
        >>> font = Font(path)
        >>> lib = font.lib

        >>> path = os.path.join(font.path, "lib.plist")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t = t.replace("<key>org.robofab.glyphOrder</key>", "<key>org.robofab.glyphOrder.XXX</key>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()

        >>> lib.keys()
        ['org.robofab.glyphOrder']
        >>> font.reloadLib()
        >>> lib.keys()
        ['org.robofab.glyphOrder.XXX']

        >>> t = t.replace("<key>org.robofab.glyphOrder.XXX</key>", "<key>org.robofab.glyphOrder</key>")
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        """
        if self._lib is None:
            obj = self.lib
        else:
            r = UFOReader(self._path)
            d = r.readLib()
            self._lib.clear()
            self._lib.update(d)
            self._stampLibDataState()

    def reloadGlyphs(self, glyphNames):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> path = getTestFontPath("TestExternalEditing.ufo")
        >>> font = Font(path)
        >>> glyph = font["A"]

        >>> path = os.path.join(font.path, "glyphs", "A_.glif")
        >>> f = open(path, "rb")
        >>> t = f.read()
        >>> f.close()
        >>> t = t.replace('<advance width="700"/>', '<advance width="701"/>')
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()

        >>> glyph.width
        700
        >>> len(glyph)
        2
        >>> font.reloadGlyphs(["A"])
        >>> glyph.width
        701
        >>> len(glyph)
        2

        >>> t = t.replace('<advance width="701"/>', '<advance width="700"/>')
        >>> f = open(path, "wb")
        >>> f.write(t)
        >>> f.close()
        """
        for glyphName in glyphNames:
            if glyphName not in self._glyphs:
                self.loadGlyph(glyphName)
            else:
                glyph = self._glyphs[glyphName]
                glyph.clear()
                pointPen = glyph.getPointPen()
                self._glyphSet.readGlyph(glyphName=glyphName, glyphObject=glyph, pointPen=pointPen)
                glyph.dirty = False
                self._stampGlyphDataState(glyph)
        self.dispatcher.postNotification(notification="Font.ReloadedGlyphs", observable=self, data=glyphNames)


if __name__ == "__main__":
    import doctest
    doctest.testmod()
