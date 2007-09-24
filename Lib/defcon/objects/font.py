from robofab.ufoLib import UFOReader, UFOWriter
from defcon.objects.base import BaseObject
from defcon.objects.glyph import Glyph
from defcon.objects.info import Info
from defcon.objects.kerning import Kerning
from defcon.objects.groups import Groups
from defcon.objects.lib import Lib


class Font(BaseObject):

    _notificationName = "Font.Changed"

    def __init__(self, path=None,
                    kerningClass=None, infoClass=None, groupsClass=None, libClass=None,
                    glyphClass=None, glyphContourClass=None):
        super(Font, self).__init__(None)
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
        #
        self._glyphClass = glyphClass
        self._glyphContourClass = glyphContourClass
        #
        self._kerningClass = kerningClass
        self._infoClass = infoClass
        self._groupsClass = groupsClass
        self._libClass = libClass
        #
        self._path = path
        #
        self._glyphs = {}
        self._glyphSet = None
        self._scheduledForDeletion = []
        #
        self._kerning = None
        self._info = None
        self._groups = None
        self._lib = None
        self.cmap = {}
        #
        self._dirty = False
        #
        if path:
            r = UFOReader(self._path)
            self._glyphSet = r.getGlyphSet()
            # glyphNameToFileNameFunc!
            self.cmap = r.getCharacterMapping()

    def _loadGlyph(self, name):
        if self._glyphSet is None or not self._glyphSet.has_key(name):
            raise KeyError, '%s not in font' % name
        glyph = self._glyphClass(self._dispatcher, contourClass=self._glyphContourClass)
        pointPen = glyph.getPointPen()
        self._glyphSet.readGlyph(glyphName=name, glyphObject=glyph, pointPen=pointPen)
        glyph.dirty = False
        self._glyphs[name] = glyph
        self._setParentDataInGlyph(glyph)
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
        glyph = self._glyphClass(self._dispatcher, contourClass=self._glyphContourClass)
        glyph.name = name
        self._glyphs[name] = glyph
        self._setParentDataInGlyph(glyph)
        self.dirty = True
        # a glyph by the same name could be
        # scheduled for deletion
        if name in self._scheduledForDeletion:
            self._scheduledForDeletion.remove(name)

    def insertGlyph(self, glyph, name=None):
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
        """
        if name not in self:
            raise KeyError, '%s not in font' % name
        if name in self._glyphs:
            del self._glyphs[name]
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
        if name in self._scheduledForDeletion:
            return False
        if self._glyphSet is not None and name in self._glyphSet:
            return True
        if name in self._glyphs:
            return True
        return False

    def keys(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> font = Font(getTestFontPath())
        >>> keys = font.keys()
        >>> keys.sort()
        >>> print keys
        ['A', 'B', 'C']
        
        >>> font = Font()
        >>> font.keys()
        []
        """
        names = set()
        if self._glyphSet is not None:
            names = names | set(self._glyphSet.keys())
        names = names | set(self._glyphs)
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

    #-----------
    # Attributes
    #-----------

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

    #------------
    # Sub-Objects
    #------------

    def _get_info(self):
        if self._info is None:
            self._info = self._infoClass(self._dispatcher)
            if self._path is not None:
                u = UFOReader(self._path)
                u.readInfo(self._info)
            self._info.setParent(self)
            self._info.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="%s.Changed" % self._info.__class__.__name__)
        return self._info

    info = property(_get_info)

    def _get_kerning(self):
        if self._kerning is None:
            self._kerning = self._kerningClass(self._dispatcher)
            if self._path is not None:
                r = UFOReader(self._path)
                d = r.readKerning()
                self._kerning.update(d)
            self._kerning.setParent(self)
            self._kerning.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="%s.Changed" % self._kerning.__class__.__name__)
        return self._kerning

    kerning = property(_get_kerning)

    def _get_groups(self):
        if self._groups is None:
            self._groups = self._groupsClass(self._dispatcher)
            if self._path is not None:
                r = UFOReader(self._path)
                d = r.readGroups()
                self._groups.update(d)
            self._groups.setParent(self)
        return self._groups

    groups = property(_get_groups)

    def _get_lib(self):
        if self._lib is None:
            self._lib = self._libClass(self._dispatcher)
            if self._path is not None:
                r = UFOReader(self._path)
                d = r.readLib()
                self._lib.update(d)
            self._lib.setParent(self)
        return self._lib

    lib = property(_get_lib)

    #--------
    # Methods
    #--------

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
            self.info.dirty = False
        if saveKerning:
            ufoWriter.writeKerning(self.kerning)
            self.kerning.dirty = False
        if saveGroups:
            ufoWriter.writeGroups(self.groups)
        if saveLib:
            ufoWriter.writeLib(self.lib)
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
        # remove deleted glyphs
        if not saveAs and self._scheduledForDeletion:
            for glyphName in self._scheduledForDeletion:
                glyphSet.deleteGlyph(glyphName)
        glyphSet.writeContents()
        self._glyphSet = glyphSet
        self._scheduledForDeletion = []
        self._path = path
        self.dirty = False

    #-----------------------
    # Notification Callbacks
    #-----------------------

    def _objectDirtyStateChange(self, notification):
        if notification.data:
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
        glyphName = notification.object().name
        self._removeFromCMAP(glyphName)
        self._addToCMAP(self[glyphName])


if __name__ == "__main__":
    import doctest
    doctest.testmod()
