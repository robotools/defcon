import os
import re
import weakref
from fontTools.misc.arrayTools import unionRect
from defcon.objects.base import BaseObject
from defcon.objects.glyph import Glyph
from defcon.objects.lib import Lib
from defcon.objects.uniData import UnicodeData
from defcon.objects.color import Color

# regular expressions used by various search methods
outlineSearchPointRE = re.compile(
    "<\s*point\s+" # <point
    "[^>]+"        # anything except >
    ">"            # >
)

componentSearchRE = re.compile(
    "<\s*component\s+"  # <component
    "[^>]*?"            # anything except >
    "base\s*=\s*[\"\']" # base="
    "(.*?)"             # glyph name
    "[\"\']"            # "
)

controlBoundsPointRE = re.compile(
    "<\s*point\s+"
    "[^>]+"
    ">"
)
controlBoundsPointXRE = re.compile(
    "\s+"
    "x\s*=\s*"
    "[\"\']"
    "([-\d]+)"
    "[\"\']"
)
controlBoundsPointYRE = re.compile(
    "\s+"
    "y\s*=\s*"
    "[\"\']"
    "([-\d]+)"
    "[\"\']"
)
controlBoundsComponentRE = re.compile(
    "<\s*component\s+"
    "[^>]*?"
    ">"
)
controlBoundsComponentBaseRE = re.compile(
    "base\s*=\s*[\"\']"
    "(.*?)"
    "[\"\']"
)
controlBoundsComponentXScaleRE = re.compile(
    "xScale\s*=\s*[\"\']"
    "([-.\d]+)"
    "[\"\']"
)
controlBoundsComponentYScaleRE = re.compile(
    "yScale\s*=\s*[\"\']"
    "([-.\d]+)"
    "[\"\']"
)
controlBoundsComponentXYScaleRE = re.compile(
    "xyScale\s*=\s*[\"\']"
    "([-.\d]+)"
    "[\"\']"
)
controlBoundsComponentYXScaleRE = re.compile(
    "yxScale\s*=\s*[\"\']"
    "([-.\d]+)"
    "[\"\']"
)
controlBoundsComponentXOffsetRE = re.compile(
    "xOffset\s*=\s*[\"\']"
    "([-\d]+)"
    "[\"\']"
)
controlBoundsComponentYOffsetRE = re.compile(
    "yOffset\s*=\s*[\"\']"
    "([-\d]+)"
    "[\"\']"
)


class Layer(BaseObject):

    changeNotificationName = "Layer.Changed"

    def __init__(self, glyphSet=None, libClass=None, unicodeDataClass=None, glyphClass=None,
                glyphContourClass=None, glyphPointClass=None, glyphComponentClass=None, glyphAnchorClass=None):
        super(Layer, self).__init__()

        self._name = None

        if glyphClass is None:
            glyphClass = Glyph
        if libClass is None:
            libClass = Lib
        if unicodeDataClass is None:
            unicodeDataClass = UnicodeData

        self._glyphClass = glyphClass
        self._glyphContourClass = glyphContourClass
        self._glyphPointClass = glyphPointClass
        self._glyphComponentClass = glyphComponentClass
        self._glyphAnchorClass = glyphAnchorClass
        self._libClass = libClass

        self._dispatcher = None
        self._color = None
        self._lib = None
        self._unicodeData = unicodeDataClass()
        self._unicodeData.setParent(self)

        self._directory = None

        self._glyphs = {}
        self._glyphSet = glyphSet
        self._scheduledForDeletion = set()
        self._keys = set()

        self._dirty = False

        if glyphSet is not None:
            self._keys = set(self._glyphSet.keys())
            cmap = {}
            for glyphName, unicodes in glyphSet.getUnicodes().items():
                for code in unicodes:
                    if code in cmap:
                        cmap[code].append(glyphName)
                    else:
                        cmap[code] = [glyphName]
            self._unicodeData.update(cmap)

    # -------------
    # Dict Behavior
    # -------------

    def _instantiateGlyphObject(self):
        glyph = self._glyphClass(
            contourClass=self._glyphContourClass,
            pointClass=self._glyphPointClass,
            componentClass=self._glyphComponentClass,
            anchorClass=self._glyphAnchorClass,
            libClass=self._libClass
        )
        return glyph

    def _loadGlyph(self, name):
        if self._glyphSet is None or not self._glyphSet.has_key(name):
            raise KeyError, "%s not in layer" % name
        glyph = self._instantiateGlyphObject()
        pointPen = glyph.getPointPen()
        self._glyphSet.readGlyph(glyphName=name, glyphObject=glyph, pointPen=pointPen)
        glyph.dirty = False
        self._glyphs[name] = glyph
        self._setParentDataInGlyph(glyph)
        self._stampGlyphDataState(glyph)
        return glyph

    def _setParentDataInGlyph(self, glyph):
        # the parent of a glyph is always the font, not the layer
        font = None
        layerSet = self.getParent()
        if layerSet is not None:
            font = layerSet.getParent()
        if font is not None:
            glyph.setParent(font)
        glyph.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Glyph.Changed")
        glyph.addObserver(observer=self, methodName="_glyphNameChange", notification="Glyph.NameChanged")
        glyph.addObserver(observer=self, methodName="_glyphUnicodesChange", notification="Glyph.UnicodesChanged")

    def _removeParentDataInGlyph(self, glyph):
        glyph.removeObserver(observer=self, notification="Glyph.Changed")
        glyph.removeObserver(observer=self, notification="Glyph.NameChanged")
        glyph.removeObserver(observer=self, notification="Glyph.UnicodesChanged")
        glyph.setParent(None)

    def newGlyph(self, name):
        """
        Create a new glyph with **name**. If a glyph with that
        name already exists, the existing glyph will be replaced
        with the new glyph.
        """
        if name in self:
            self._unicodeData.removeGlyphData(name, self[name].unicodes)
        glyph = self._instantiateGlyphObject()
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
        Insert **glyph** into the layer. Optionally, the glyph
        can be renamed at the same time by providing **name**.
        If a glyph with the glyph name, or the name provided
        as **name**, already exists, the existing glyph will
        be replaced with the new glyph.
        """
        # DO NOT ACTUALLY INSERT THE GLYPH!
        # it is crucially important that the data be reconstructed
        # in its entirety so that the parent data is properly set
        # in all of the various objects.
        from copy import deepcopy
        source = glyph
        if name is None:
            name = source.name
        self.newGlyph(name)
        dest = self[name]
        # advance
        dest.width = source.width
        dest.height = source.height
        # unicodes
        dest.unicodes = list(source.unicodes)
        # note
        dest.note = source.note
        # guidelines
        dest.guidelines = glyph.guidelines
        # anchors
        dest.anchors = glyph.anchors
        # image
        dest.image = glyph.image
        # contours and components
        pointPen = dest.getPointPen()
        source.drawPoints(pointPen)
        # lib
        dest.lib = deepcopy(source.lib)
        # update self.unicodeData
        if dest.unicodes:
            self._unicodeData.addGlyphData(name, dest.unicodes)
        return dest

    def __iter__(self):
        names = self.keys()
        while names:
            name = names[0]
            yield self[name]
            names = names[1:]

    def __getitem__(self, name):
        if name not in self._glyphs:
            self._loadGlyph(name)
        return self._glyphs[name]

    def __delitem__(self, name):
        if name not in self:
            raise KeyError, "%s not in layer" % name
        self._unicodeData.removeGlyphData(name, self[name].unicodes)
        if name in self._glyphs:
            glyph = self._glyphs.pop(name)
            self._removeParentDataInGlyph(glyph)
        if name in self._keys:
            self._keys.remove(name)
        if self._glyphSet is not None and name in self._glyphSet:
            self._scheduledForDeletion.add(name)
        self.dirty = True

    def __len__(self):
        return len(self.keys())

    def __contains__(self, name):
        return name in self._keys

    def keys(self):
        """
        The names of all glyphs in the layer.
        """
        # this is not generated dynamically since we
        # support external editing. it must be fixed.
        names = self._keys
        names = names - self._scheduledForDeletion
        return list(names)

    # ----------
    # Attributes
    # ----------

    def _set_name(self, value):
        oldName = self._name
        if oldName != value:
            self._name = value
            data = dict(oldName=oldName, newName=value)
            self.postNotification(notification="Layer.NameChanged", data=data)
            self.dirty = True

    def _get_name(self):
        return self._name

    name = property(_get_name, _set_name, doc="The name of the layer. Setting this posts *Layer.NameChanged* and *Layer.Changed* notifications.")

    def _get_color(self):
        return self._color

    def _set_color(self, color):
        if color is None:
            newColor = None
        else:
            newColor = Color(color)
        oldColor = self._color
        if oldColor != newColor:
            self._color = newColor
            data = dict(oldColor=oldColor, newColor=newColor)
            self.postNotification(notification="Layer.ColorChanged", data=data)
            self.dirty = True

    color = property(_get_color, _set_color, doc="The layer's :class:`Color` object. When setting, the value can be a UFO color string, a sequence of (r, g, b, a) or a :class:`Color` object. Setting this posts *Layer.ColorChanged* and *Layer.Changed* notifications.")

    def _get_glyphsWithOutlines(self):
        found = []
        # scan loaded glyphs
        for glyphName, glyph in self._glyphs.items():
            if glyphName in self._scheduledForDeletion:
                continue
            if len(glyph):
                found.append(glyphName)
        # scan glyphs that have not been loaded
        if self._glyphSet is not None:
            for glyphName, fileName in self._glyphSet.contents.items():
                if glyphName in self._glyphs or glyphName in self._scheduledForDeletion:
                    continue
                # get the raw GLIF
                data = self._glyphSet.getGLIF(glyphName)
                containsPoints = False
                # use an re to extract all points
                points = outlineSearchPointRE.findall(data)
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

    glyphsWithOutlines = property(_get_glyphsWithOutlines, doc="A list of glyphs containing outlines.")

    def _get_componentReferences(self):
        found = {}
        # scan loaded glyphs
        for glyphName, glyph in self._glyphs.items():
            if glyphName in self._scheduledForDeletion:
                continue
            if not glyph.components:
                continue
            for component in glyph.components:
                baseGlyph = component.baseGlyph
                if baseGlyph not in found:
                    found[baseGlyph] = set()
                found[baseGlyph].add(glyphName)
        # scan glyphs that have not been loaded
        if self._glyphSet is not None:
            for glyphName, fileName in self._glyphSet.contents.items():
                if glyphName in self._glyphs or glyphName in self._scheduledForDeletion:
                    continue
                data = self._glyphSet.getGLIF(glyphName)
                baseGlyphs = componentSearchRE.findall(data)
                for baseGlyph in baseGlyphs:
                    if baseGlyph not in found:
                        found[baseGlyph] = set()
                    found[baseGlyph].add(glyphName)
        return found

    componentReferences = property(_get_componentReferences, doc="A dict of describing the component relationships in the layer. The dictionary is of form ``{base glyph : [references]}``.")

    def _get_bounds(self):
        fontRect = None
        for glyph in self:
            glyphRect = glyph.bounds
            if glyphRect is None:
                continue
            if fontRect is None:
                fontRect = glyphRect
            else:
                fontRect = unionRect(fontRect, glyphRect)
        return fontRect

    bounds = property(_get_bounds, doc="The bounds of all glyphs in the layer. This can be an expensive operation.")

    def _get_controlPointBounds(self):
        from fontTools.misc.transform import Transform
        # storage
        glyphRects = {}
        componentReferences = {}
        # scan loaded glyphs
        for glyphName, glyph in self._glyphs.items():
            if glyphName in self._scheduledForDeletion:
                continue
            glyphRect = glyph.controlPointBounds
            if glyphRect:
                glyphRects[glyphName] = glyphRect
        # scan glyphs that have not been loaded
        if self._glyphSet is not None:
            for glyphName, fileName in self._glyphSet.contents.items():
                if glyphName in self._glyphs or glyphName in self._scheduledForDeletion:
                    continue
                # get the GLIF text
                data = self._glyphSet.getGLIF(glyphName)
                # get the point bounding box
                xMin = None
                xMax = None
                yMin = None
                yMax = None
                for line in controlBoundsPointRE.findall(data):
                    x = controlBoundsPointXRE.findall(line)
                    if not x:
                        continue
                    y = controlBoundsPointYRE.findall(line)
                    if not y:
                        continue
                    x = int(x[0])
                    if xMin is None:
                        xMin = xMax = x
                    if xMin > x:
                        xMin = x
                    if xMax < x:
                        xMax = x
                    y = int(y[0])
                    if yMin is None:
                        yMin = yMax = y
                    if yMin > y:
                        yMin = y
                    if yMax < y:
                        yMax = y
                glyphRect = (xMin, yMin, xMax, yMax)
                if None not in glyphRect:
                    glyphRects[glyphName] = glyphRect
                # get all component references
                for line in controlBoundsComponentRE.findall(data):
                    base = controlBoundsComponentBaseRE.findall(line)
                    if not base:
                        continue
                    base = base[0]
                    # xScale
                    xScale = controlBoundsComponentXScaleRE.findall(line)
                    if not xScale:
                        xScale = [1]
                    xScale = float(xScale[0])
                    # yScale
                    yScale = controlBoundsComponentYScaleRE.findall(line)
                    if not yScale:
                        yScale = [1]
                    yScale = float(yScale[0])
                    # xyScale
                    xyScale = controlBoundsComponentXYScaleRE.findall(line)
                    if not xyScale:
                        xyScale = [0]
                    xyScale = float(xyScale[0])
                    # yxScale
                    yxScale = controlBoundsComponentYXScaleRE.findall(line)
                    if not yxScale:
                        yxScale = [0]
                    yxScale = float(yxScale[0])
                    # xOffset
                    xOffset = controlBoundsComponentXOffsetRE.findall(line)
                    if not xOffset:
                        xOffset = [0]
                    xOffset = int(xOffset[0])
                    # yOffset
                    yOffset = controlBoundsComponentYOffsetRE.findall(line)
                    if not yOffset:
                        yOffset = [0]
                    yOffset = int(yOffset[0])
                    if glyphName not in componentReferences:
                        componentReferences[glyphName] = []
                    componentReferences[glyphName].append((base, xScale, xyScale, yxScale, yScale, xOffset, yOffset))
        # get the transformed component bounding boxes and update the glyphs
        for glyphName, components in componentReferences.items():
            glyphRect = glyphRects.get(glyphName, (None, None, None, None))
            # XXX this doesn't handle nested components
            for base, xScale, xyScale, yxScale, yScale, xOffset, yOffset in components:
                # base glyph doesn't exist
                if base not in glyphRects:
                    continue
                baseRect = glyphRects[base]
                # base glyph has no points
                if None in baseRect:
                    continue
                # transform the base rect
                transform = Transform(xx=xScale, xy=xyScale, yx=yxScale, yy=yScale, dx=xOffset, dy=yOffset)
                xMin, yMin, xMax, yMax = baseRect
                (xMin, yMin), (xMax, yMax) = transform.transformPoints([(xMin, yMin), (xMax, yMax)])
                componentRect = (xMin, yMin, xMax, yMax)
                # update the glyph rect
                if None in glyphRect:
                    glyphRect = componentRect
                else:
                    glyphRect = unionRect(glyphRect, componentRect)
            # store the updated rect
            glyphRects[glyphName] = glyphRect
        # work out the unified rect
        fontRect = None
        for glyphRect in glyphRects.values():
            if fontRect is None:
                fontRect = glyphRect
            elif glyphRect is not None:
                fontRect = unionRect(fontRect, glyphRect)
        # done
        return fontRect

    controlPointBounds = property(_get_controlPointBounds, doc="The control bounds of all glyphs in the layer. This only measures the point positions, it does not measure curves. So, curves without points at the extrema will not be properly measured. This is an expensive operation.")

    # -----------
    # Sub-Objects
    # -----------

    def _get_lib(self):
        if self._lib is None:
            self._lib = self._libClass()
            self._lib.setParent(self)
            self._lib.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Lib.Changed")
        return self._lib

    def _set_lib(self, value):
        if value is not None:
            self.lib.clear()
            self.lib.update(value)

    lib = property(_get_lib, _set_lib, doc="The layer's :class:`Lib` object.")

    def _get_unicodeData(self):
        return self._unicodeData

    unicodeData = property(_get_unicodeData, doc="The layer's :class:`UnicodeData` object.")

    # -------
    # Methods
    # -------

    def save(self, glyphSet, saveAs=False, progressBar=None):
        # for a save as operation, load all the glyphs
        # and mark them as dirty. this could be more
        # effeciently handled by os.copy...
        if saveAs:
            for glyph in self:
                glyph.dirty = True
        for glyphName, glyph in sorted(self._glyphs.items()):
            self.saveGlyph(glyph, glyphSet, saveAs=saveAs, progressBar=progressBar)
        # remove deleted glyphs
        if not saveAs and self._scheduledForDeletion:
            for glyphName in self._scheduledForDeletion:
                if glyphName in glyphSet:
                    glyphSet.deleteGlyph(glyphName)
        glyphSet.writeContents()
        self._glyphSet = glyphSet
        self._scheduledForDeletion.clear()

    def saveGlyph(self, glyph, glyphSet, saveAs=False, progressBar=None):
        if glyph.dirty:
            glyphSet.writeGlyph(glyph.name, glyph, glyph.drawPoints)
            self._stampGlyphDataState(glyph)

    # ---------------------
    # External Edit Support
    # ---------------------

    # data stamping

    def _stampGlyphDataState(self, glyph):
        pass
        #if self._glyphSet is None:
        #    return
        #glyphSet = self._glyphSet
        #glyphName = glyph.name
        #if glyphName not in glyphSet.contents:
        #    return
        #path = os.path.join(self.path, "glyphs", glyphSet.contents[glyphName])
        ## get the text
        #f = open(path, "rb")
        #text = f.read()
        #f.close()
        ## get the file modification time
        #modTime = os.stat(path).st_mtime
        ## store the data
        #glyph._dataOnDisk = text
        #glyph._dataOnDiskTimeStamp = modTime

    # ----------------------
    # Notification Callbacks
    # ----------------------

    def _objectDirtyStateChange(self, notification):
        if notification.object.dirty:
            self.dirty = True

    def _glyphNameChange(self, notification):
        data = notification.data
        oldName = data["oldName"]
        newName = data["newName"]
        glyph = self._glyphs[oldName]
        del self[oldName]
        self._glyphs[newName] = glyph
        self._keys.add(newName)
        self._unicodeData.removeGlyphData(oldName, glyph.unicodes)
        self._unicodeData.addGlyphData(newName, glyph.unicodes)

    def _glyphUnicodesChange(self, notification):
        glyphName = notification.object.name
        data = notification.data
        oldValues = data["oldValues"]
        newValues = data["newValues"]
        self._unicodeData.removeGlyphData(glyphName, oldValues)
        self._unicodeData.addGlyphData(glyphName, newValues)


# -----
# Tests
# -----

def _testSetParentDataInGlyph():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> glyph = layer['A']
    >>> id(glyph.getParent()) == id(font)
    True
    """

def _testNewGlyph():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> layer.newGlyph('NewGlyphTest')
    >>> glyph = layer['NewGlyphTest']
    >>> glyph.name
    'NewGlyphTest'
    >>> glyph.dirty
    True
    >>> font.dirty
    True
    >>> keys = layer.keys()
    >>> keys.sort()
    >>> keys
    ['A', 'B', 'C', 'NewGlyphTest']
    """

def _testInsertGlyph():
    """
    >>> "need insert glyph test!"
    """

def _testIter():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> names = [glyph.name for glyph in layer]
    >>> names.sort()
    >>> names
    ['A', 'B', 'C']
    >>> names = []
    >>> for glyph1 in layer:
    ...     for glyph2 in layer:
    ...         names.append((glyph1.name, glyph2.name))
    >>> names.sort()
    >>> names
    [('A', 'A'), ('A', 'B'), ('A', 'C'), ('B', 'A'), ('B', 'B'), ('B', 'C'), ('C', 'A'), ('C', 'B'), ('C', 'C')]
    """

def _testGetitem():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> layer['A'].name
    'A'
    >>> layer['B'].name
    'B'
    >>> layer['NotInFont']
    Traceback (most recent call last):
        ...
    KeyError: 'NotInFont not in layer'
    """

def _testDelitem():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> import glob
    >>> import os
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> layer = font.layers["public.default"]
    >>> glyph = layer['A']
    >>> del layer['A']
    >>> glyph.getParent()
    >>> layer.dirty
    True
    >>> layer.newGlyph('NewGlyphTest')
    >>> del layer['NewGlyphTest']
    >>> keys = layer.keys()
    >>> keys.sort()
    >>> keys
    ['B', 'C']
    >>> len(layer)
    2
    >>> 'A' in layer
    False
    >>> font.save()
    >>> fileNames = glob.glob(os.path.join(path, 'Glyphs', '*.glif'))
    >>> fileNames = [os.path.basename(fileName) for fileName in fileNames]
    >>> fileNames.sort()
    >>> fileNames
    ['B_.glif', 'C_.glif']
    >>> del layer['NotInFont']
    Traceback (most recent call last):
        ...
    KeyError: 'NotInFont not in layer'
    >>> tearDownTestFontCopy()

#    # test saving externally deleted glyphs.
#    # del glyph. not dirty.
#    >>> path = makeTestFontCopy()
#    >>> font = Font(path)
#    >>> layer = font.layers["public.default"]
#    >>> glyph = layer["A"]
#    >>> glyphPath = os.path.join(path, "glyphs", "A_.glif")
#    >>> os.remove(glyphPath)
#    >>> r = font.testForExternalChanges()
#    >>> r["deletedGlyphs"]
#    ['A']
#    >>> del layer["A"]
#    >>> font.save()
#    >>> os.path.exists(glyphPath)
#    False
#    >>> tearDownTestFontCopy()

#    # del glyph. dirty.
#    >>> path = makeTestFontCopy()
#    >>> font = Font(path)
#    >>> layer = font.layers["public.default"]
#    >>> glyph = layer["A"]
#    >>> glyph.dirty = True
#    >>> glyphPath = os.path.join(path, "glyphs", "A_.glif")
#    >>> os.remove(glyphPath)
#    >>> r = font.testForExternalChanges()
#    >>> r["deletedGlyphs"]
#    ['A']
#    >>> del layer["A"]
#    >>> font.save()
#    >>> os.path.exists(glyphPath)
#    False
#    >>> tearDownTestFontCopy()
    """

def _testLen():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> len(layer)
    3

    >>> font = Font()
    >>> layer = font.layers["public.default"]
    >>> len(layer)
    0
    """

def _testContains():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> 'A' in layer
    True
    >>> 'NotInFont' in layer
    False

    >>> font = Font()
    >>> layer = font.layers["public.default"]
    >>> 'A' in layer
    False
    """

def _testKeys():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> keys = layer.keys()
    >>> keys.sort()
    >>> print keys
    ['A', 'B', 'C']
    >>> del layer["A"]
    >>> keys = layer.keys()
    >>> keys.sort()
    >>> print keys
    ['B', 'C']
    >>> layer.newGlyph("A")
    >>> keys = layer.keys()
    >>> keys.sort()
    >>> print keys
    ['A', 'B', 'C']

    >>> font = Font()
    >>> layer = font.layers["public.default"]
    >>> layer.keys()
    []
    >>> layer.newGlyph("A")
    >>> keys = layer.keys()
    >>> keys.sort()
    >>> print keys
    ['A']
    """

def _testColor():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["Layer 1"]
    >>> isinstance(layer.color, Color)
    True
    >>> str(layer.color)
    '0.1,0.2,0.3,0.4'
    >>> layer.color = '0.5,0.5,0.5,0.5'
    >>> isinstance(layer.color, Color)
    True
    >>> str(layer.color)
    '0.5,0.5,0.5,0.5'
    >>> layer.color = (.5, .5, .5, .5)
    >>> isinstance(layer.color, Color)
    True
    >>> str(layer.color)
    '0.5,0.5,0.5,0.5'
    """

def _testLib():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["Layer 1"]
    >>> layer.lib
    {'com.typesupply.defcon.test': '1 2 3'}
    >>> layer.lib.dirty = False
    >>> layer.lib["blah"] = "abc"
    >>> layer.lib["blah"]
    'abc'
    >>> layer.lib.dirty
    True
    """

def _testGlyphWithOutlines():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> sorted(layer.glyphsWithOutlines)
    ['A', 'B']
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> for glyph in layer:
    ...    pass
    >>> sorted(layer.glyphsWithOutlines)
    ['A', 'B']
    """

def _testComponentReferences():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> layer.componentReferences
    {'A': set(['C']), 'B': set(['C'])}
    >>> glyph = layer["C"]
    >>> layer.componentReferences
    {'A': set(['C']), 'B': set(['C'])}
    """

def _testBounds():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> layer.bounds
    (0, 0, 700, 700)
    """

def _testControlPointBounds():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> layer.controlPointBounds
    (0, 0, 700, 700)
    """

def _testGlyphNameChange():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> glyph = layer['A']
    >>> glyph.name = 'NameChangeTest'
    >>> keys = layer.keys()
    >>> keys.sort()
    >>> keys
    ['B', 'C', 'NameChangeTest']
    >>> layer.dirty
    True
    """

def _testGlyphUnicodesChanged():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> glyph = layer['A']
    >>> glyph.unicodes = [123, 456]
    >>> layer.unicodeData[123]
    ['A']
    >>> layer.unicodeData[456]
    ['A']
    >>> layer.unicodeData[66]
    ['B']
    >>> layer.unicodeData.get(65)

    >>> font = Font(getTestFontPath())
    >>> layer = font.layers["public.default"]
    >>> layer.newGlyph("test")
    >>> glyph = layer["test"]
    >>> glyph.unicodes = [65]
    >>> layer.unicodeData[65]
    ['A', 'test']
    """

def _testGlyphDispatcher():
    """
    >>> from defcon import Font, Component, Anchor, Guideline
    >>> from defcon.test.testTools import getTestFontPath

    # loaded
    >>> font = Font(getTestFontPath())
    >>> glyph = font["A"]
    >>> glyph.dispatcher is not None
    True
    >>> glyph.dispatcher == font.dispatcher
    True
    >>> contour = glyph[0]
    >>> contour.getParent() == glyph
    True
    >>> contour.dispatcher == font.dispatcher
    True
    >>> anchor = glyph.anchors[0]
    >>> anchor.getParent() == glyph
    True
    >>> anchor.dispatcher == font.dispatcher
    True
    >>> glyph = font["C"]
    >>> component = glyph.components[0]
    >>> component.getParent() == glyph
    True
    >>> component.dispatcher == font.dispatcher
    True
    >>> glyph = font.layers["Layer 1"]["A"]
    >>> guideline = glyph.guidelines[0]
    >>> guideline.getParent() == glyph
    True
    >>> guideline.dispatcher == font.dispatcher
    True

    # new
    >>> font = Font()
    >>> font.newGlyph("A")
    >>> glyph = font["A"]
    >>> pen = glyph.getPointPen()
    >>> pen.beginPath()
    >>> pen.addPoint((0, 0), segmentType="line")
    >>> pen.addPoint((0, 100), segmentType="line")
    >>> pen.addPoint((100, 100), segmentType="line")
    >>> pen.addPoint((100, 0), segmentType="line")
    >>> pen.endPath()
    >>> contour = glyph[0]
    >>> contour.getParent() == glyph
    True
    >>> contour.dispatcher == font.dispatcher
    True
    >>> component = Component()
    >>> glyph.appendComponent(component)
    >>> component.getParent() == glyph
    True
    >>> component.dispatcher == font.dispatcher
    True
    >>> anchor = Anchor()
    >>> glyph.appendAnchor(anchor)
    >>> anchor.getParent() == glyph
    True
    >>> anchor.dispatcher == font.dispatcher
    True
    >>> guideline = Guideline()
    >>> glyph.appendGuideline(guideline)
    >>> guideline.getParent() == glyph
    True
    >>> guideline.dispatcher == font.dispatcher
    True

    # inserted
    >>> sourceGlyph = glyph
    >>> newFont = Font()
    >>> insertedGlyph = newFont.insertGlyph(sourceGlyph)
    >>> contour = insertedGlyph[0]
    >>> contour.getParent() == insertedGlyph
    True
    >>> contour.dispatcher == newFont.dispatcher
    True
    >>> component = insertedGlyph.components[0]
    >>> component.getParent() == insertedGlyph
    True
    >>> component.dispatcher == newFont.dispatcher
    True
    >>> anchor = insertedGlyph.anchors[0]
    >>> anchor.getParent() == insertedGlyph
    True
    >>> anchor.dispatcher == newFont.dispatcher
    True
    >>> guideline = insertedGlyph.guidelines[0]
    >>> guideline.getParent() == insertedGlyph
    True
    >>> guideline.dispatcher == newFont.dispatcher
    True
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()