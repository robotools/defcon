import os
import re
import weakref
from fontTools.misc.arrayTools import unionRect
from defcon.objects.base import BaseObject
from defcon.objects.glyph import Glyph
from defcon.objects.lib import Lib
from defcon.objects.uniData import UnicodeData
from defcon.tools.notifications import NotificationCenter


class LayerSet(BaseObject):

    changeNotificationName = "LayerSet.Changed"

    def __init__(self, layerClass=None, glyphClass=None,
            glyphContourClass=None, glyphPointClass=None, glyphComponentClass=None, glyphAnchorClass=None):
        super(LayerSet, self).__init__()
        if layerClass is None:
            layerClass = Layer

        self._layerClass = layerClass
        self._glyphClass = glyphClass
        self._glyphContourClass = glyphContourClass
        self._glyphPointClass = glyphPointClass
        self._glyphComponentClass = glyphComponentClass
        self._glyphAnchorClass = glyphAnchorClass

        self._layers = {}
        self._layerOrder = []
        self._defaultLayer = None

        self._renamedLayers = {}
        self._scheduledForDeletion = []

    def _get_defaultLayer(self):
        return self._defaultLayer

    def _set_defaultLayer(self, layer):
        if layer is None:
            raise DefconError("The default layer must not be None.")
        if layer == self._defaultLayer:
            return
        self._defaultLayer = layer
        self.positions
        layer.dirty = True

    defaultLayer = property(_get_defaultLayer, _set_defaultLayer, doc="The default :class:`Layer` object.")

    # ----------------
    # Layer Management
    # ----------------

    def _instantiateLayerObject(self):
        layer = self._layerClass(
            glyphClass=self._glyphClass,
            contourClass=self._glyphContourClass,
            pointClass=self._glyphPointClass,
            componentClass=self._glyphComponentClass,
            anchorClass=self._glyphAnchorClass,
            libClass=self._libClass
        )
        return layer

    def newLayer(self, name):
        """
        Create a new :class:`Layer` and add
        it to the top of the layer order.
        """
        if name in self._layers:
            raise KeyError("A layer named \"%s\" already exists." % name)
        layer = self._instantiateLayerObject()
        layer.setParent(self)
        self._layers[name] = layer
        self._layerOrder.insert(0, name)
        self.dirty = True
        return layer



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
        super(layer, self).__init__()
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
        self._lib = None
        self._unicodeData = unicodeDataClass()

        self._directory = None

        self._glyphs = {}
        self._glyphSet = glyphSet
        self._scheduledForDeletion = []
        self._keys = set()

        self._dirty = False

        if glyphSet is not None:
            self._keys = set(self._glyphSet.keys())
            self._unicodeData.update(reader.getCharacterMapping())

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
        font = self.getParent()
        glyph.setParent(font)
        glyph.dispatcher = self.dispatcher
        glyph.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Glyph.Changed")
        glyph.addObserver(observer=self, methodName="_glyphNameChange", notification="Glyph.NameChanged")
        glyph.addObserver(observer=self, methodName="_glyphUnicodesChange", notification="Glyph.UnicodesChanged")

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
            del self._glyphs[name]
        if name in self._keys:
            self._keys.remove(name)
        if self._glyphSet is not None and name in self._glyphSet:
            self._scheduledForDeletion.append(name)
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
        names = names - set(self._scheduledForDeletion)
        return list(names)

    # ----------
    # Attributes
    # ----------

    def _get_name(self):
        return self._name

    def _set_name(self, name):
        self._name = name
        self.dirty = True

    name = property(_get_name, _set_name, doc="The layer's name.")

    def _get_directory(self):
        return self._directory

    directory = property(_get_directory, doc="The layer's directory name from the UFO at the last read or write operation.")

    def _get_fillColor(self):
        return self._fillColor

    def _set_fillColor(self, fillColor):
        self._fillColor = fillColor
        self.dirty = True

    fillColor = property(_get_fillColor, _set_fillColor, doc="The layer's fill color.")

    def _get_strokeColor(self):
        return self._strokeColor

    def _set_strokeColor(self, strokeColor):
        self._strokeColor = strokeColor
        self.dirty = True

    strokeColor = property(_get_strokeColor, _set_strokeColor, doc="The layer's strokeColor.")
    def _get_strokeWidth(self):
        return self._strokeWidth

    def _set_strokeWidth(self, strokeWidth):
        self._strokeWidth = strokeWidth
        self.dirty = True

    strokeWidth = property(_get_strokeWidth, _set_strokeWidth, doc="The layer's stroke width.")

    def _get_glyphsWithOutlines(self):
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
        if self.path is not None:
            glyphsPath = os.path.join(self.path, "glyphs")
            for glyphName, fileName in self._glyphSet.contents.items():
                if glyphName in self._glyphs or glyphName in self._scheduledForDeletion:
                    continue
                glyphPath = os.path.join(glyphsPath, fileName)
                f = open(glyphPath, "rb")
                data = f.read()
                f.close()
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
        if self.path is not None:
            glyphsPath = os.path.join(self.path, "glyphs")
            for glyphName, fileName in self._glyphSet.contents.items():
                if glyphName in self._glyphs or glyphName in self._scheduledForDeletion:
                    continue
                # get the GLIF text
                glyphPath = os.path.join(glyphsPath, fileName)
                f = open(glyphPath, "rb")
                data = f.read()
                f.close()
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
            self._lib.dispatcher = self.dispatcher
            self._lib.setParent(self)
            if self._path is not None:
                reader = ufoLib.UFOReader(self._path)
                d = reader.readLib()
                self._lib.update(d)
            self._lib.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Lib.Changed")
            self._stampLibDataState()
        return self._lib

    lib = property(_get_lib, doc="The layer's :class:`Lib` object.")

    def _get_unicodeData(self):
        return self._unicodeData

    unicodeData = property(_get_unicodeData, doc="The layer's :class:`UnicodeData` object.")

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

    