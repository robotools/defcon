from fontTools.misc import arrayTools
from defcon.objects.base import BaseObject
from defcon.tools.fuzzyNumber import FuzzyNumber
from defcon.tools.notifications import NotificationCenter


_representationFactories = {}

def addRepresentationFactory(name, factory):
    _representationFactories[name] = factory

def removeRepresentationFactory(name):
    del _representationFactories[name]


class Glyph(BaseObject):

    _notificationName = "Glyph.Changed"

    def __init__(self, dispatcher=None, contourClass=None, componentClass=None, anchorClass=None):
        super(Glyph, self).__init__()
        self._parent = None
        self._dirty = False
        self._name = None
        self._unicodes = []
        self._width = 0
        self.note = None
        self.lib = {}
        self._dispatcher = dispatcher

        self._contours = []
        self._components = []
        self._anchors = []

        self._boundsCache = None

        self._representations = {}

        if contourClass is None:
            from contour import Contour
            contourClass = Contour
        if componentClass is None:
            from component import Component
            componentClass = Component
        if anchorClass is None:
            from anchor import Anchor
            anchorClass = Anchor

        self.contourClass = contourClass
        self.componentClass = componentClass
        self.anchorClass = anchorClass

        if dispatcher is not None:
            self.addObserver(observer=self, methodName="destroyAllRepresentations", notification="Glyph.Changed")

    def _set_dispatcher(self, dispatcher):
        super(Glyph, self)._set_dispatcher(dispatcher)
        if dispatcher is not None:
            for contour in self._contours:
                self._setParentDataInContour(contour)
            for component in self._components:
                self._setParentDataInComponent(component)
            for anchor in self._anchors:
                self._setParentDataInAnchor(anchor)

    def _get_dispatcher(self):
        return super(Glyph, self)._get_dispatcher()

    dispatcher = property(_get_dispatcher, _set_dispatcher)

    # ----------
    # Attributes
    # ----------

    def _set_name(self, value):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.name = 'RenamedGlyph'
        >>> glyph.name
        'RenamedGlyph'
        >>> keys = font.keys()
        >>> keys.sort()
        >>> keys
        ['B', 'C', 'RenamedGlyph']

        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.name = 'A'
        >>> glyph.dirty
        False
        >>> font._scheduledForDeletion
        []
        """
        oldName = self._name
        if oldName != value:
            self._name = value
            self.dirty = True
            dispatcher = self.dispatcher
            if dispatcher is not None:
                self.dispatcher.postNotification(notification="Glyph.NameChanged", observable=self, data=(oldName, value))

    def _get_name(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.name
        'A'
        """
        return self._name

    name = property(_get_name, _set_name)

    def _get_unicodes(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.unicodes
        [65]
        """
        return list(self._unicodes)

    def _set_unicodes(self, value):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.unicodes = [123, 456]
        >>> glyph.unicodes
        [123, 456]
        >>> glyph.dirty
        True
        """
        oldValue = self.unicodes
        if oldValue != value:
            self._unicodes = value
            self.dirty = True
            dispatcher = self.dispatcher
            if dispatcher is not None:
                self.dispatcher.postNotification(notification="Glyph.UnicodesChanged", observable=self, data=(oldValue, value))

    unicodes = property(_get_unicodes, _set_unicodes)

    def _get_unicode(self):
        if self._unicodes:
            return self._unicodes[0]
        return None

    def _set_unicode(self, value):
        unicodes = [value] + list(self._unicodes)
        self.unicodes = unicodes

    unicode = property(_get_unicode, _set_unicode)

    def _get_bounds(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.bounds
        (0, 0, 700, 700)
        >>> glyph = font['B']
        >>> glyph.bounds
        (0, 0, 700, 700)
        >>> glyph = font['C']
        >>> glyph.bounds
        (0, 0, 700, 700)
        """
        from robofab.pens.boundsPen import BoundsPen
        if self._boundsCache is None:
            pen = BoundsPen(self.getParent())
            self.draw(pen)
            self._boundsCache = pen.bounds
        return self._boundsCache

    bounds = property(_get_bounds)

    def _get_leftMargin(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.leftMargin
        0
        >>> glyph = font['B']
        >>> glyph.leftMargin
        0
        """
        bounds = self.bounds
        if bounds is None:
            return None
        xMin, yMin, xMax, yMax = bounds
        return xMin

    def _set_leftMargin(self, value):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.leftMargin = 100
        >>> glyph.leftMargin
        100
        >>> glyph.dirty
        True
        """
        bounds = self.bounds
        if bounds is None:
            return
        xMin, yMin, xMax, yMax = bounds
        diff = value - xMin
        self.move((diff, 0))
        self._width += diff

    leftMargin = property(_get_leftMargin, _set_leftMargin)

    def _get_rightMargin(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.rightMargin
        0
        """
        bounds = self.bounds
        if bounds is None:
            return None
        xMin, yMin, xMax, yMax = bounds
        return self._width - xMax

    def _set_rightMargin(self, value):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.rightMargin = 100
        >>> glyph.rightMargin
        100
        >>> glyph.width
        800
        >>> glyph.dirty
        True
        """
        bounds = self.bounds
        if bounds is None:
            return
        xMin, yMin, xMax, yMax = bounds
        self._width = xMax + value
        self.dirty = True

    rightMargin = property(_get_rightMargin, _set_rightMargin)

    def _get_width(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.width
        700
        """
        return self._width

    def _set_width(self, value):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.width = 100
        >>> glyph.width
        100
        >>> glyph.dirty
        True
        """
        self._width = value
        self.dirty = True

    width = property(_get_width, _set_width)

    def _get_components(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['C']
        >>> len(glyph.components)
        2
        """
        return list(self._components)

    components = property(_get_components)

    def _get_anchors(self):
        """
        >>> print 'Need Anchor Test!'
        """
        return list(self._anchors)

    anchors = property(_get_anchors)

    # -----------
    # Pen Methods
    # -----------

    def draw(self, pen):
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        for contour in self._contours:
            contour.drawPoints(pointPen)
        for component in self._components:
            component.drawPoints(pointPen)
        for anchor in self._anchors:
            anchor.drawPoints(pointPen)

    def getPen(self):
        from robofab.pens.adapterPens import SegmentToPointPen
        return SegmentToPointPen(self.getPointPen())

    def getPointPen(self):
        from defcon.pens.glyphObjectPointPen import GlyphObjectPointPen
        return GlyphObjectPointPen(self)

    # -------
    # Methods
    # -------

    def __len__(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> len(glyph)
        2
        """
        return len(self._contours)

    def __iter__(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> for contour in glyph:
        ...     print len(contour)
        4
        4
        """
        contourCount =len(self)
        index = 0
        while index < contourCount:
            contour = self[index]
            yield contour
            index += 1    

    def __getitem__(self, index):
        return self._contours[index]

    def _getContourIndex(self, contour):
        return self._contours.index(contour)

    def _setParentDataInContour(self, contour):
        contour.setParent(self)
        dispatcher = self.dispatcher
        if dispatcher is not None:
            contour.dispatcher = dispatcher
            contour.addObserver(observer=self, methodName="_outlineContentChanged", notification="Contour.Changed")

    def _removeParentDataInContour(self, contour):
        contour.setParent(None)
        contour.removeObserver(observer=self, notification="Contour.Changed")
        contour._dispatcher = None

    def _setParentDataInComponent(self, component):
        component.setParent(self)
        dispatcher = self.dispatcher
        if dispatcher is not None:
            component.dispatcher = dispatcher
            component.addObserver(observer=self, methodName="_outlineContentChanged", notification="Component.Changed")

    def _removeParentDataInComponent(self, component):
        component.setParent(None)
        component.removeObserver(observer=self, notification="Component.Changed")
        component._dispatcher = None

    def _setParentDataInAnchor(self, anchor):
        anchor.setParent(self)
        dispatcher = self.dispatcher
        if dispatcher is not None:
            anchor.dispatcher = dispatcher
            anchor.addObserver(observer=self, methodName="_outlineContentChanged", notification="Anchor.Changed")

    def appendContour(self, contour):
        """
        >>> from defcon.objects.contour import Contour
        >>> glyph = Glyph()
        >>> glyph.dirty = False
        >>> contour = Contour()
        >>> glyph.appendContour(contour)
        >>> len(glyph)
        1
        >>> glyph.dirty
        True
        """
        assert contour not in self._contours
        self._setParentDataInContour(contour)
        self._contours.append(contour)
        self._boundsCache = None
        self.dirty = True

    def appendComponent(self, component):
        """
        >>> from defcon.objects.component import Component
        >>> glyph = Glyph()
        >>> glyph.dirty = False
        >>> component = Component()
        >>> glyph.appendComponent(component)
        >>> len(glyph.components)
        1
        >>> glyph.dirty
        True
        """
        assert component not in self._components
        self._setParentDataInComponent(component)
        self._components.append(component)
        self._boundsCache = None
        self.dirty = True

    def appendAnchor(self, anchor):
        """
        >>> from defcon.objects.anchor import Anchor
        >>> glyph = Glyph()
        >>> glyph.dirty = False
        >>> anchor = Anchor()
        >>> glyph.appendAnchor(anchor)
        >>> len(glyph.anchors)
        1
        >>> glyph.dirty
        True
        """
        assert anchor not in self._anchors
        self._setParentDataInAnchor(anchor)
        self._anchors.append(anchor)
        self.dirty = True

    def insertContour(self, index, contour):
        assert contour not in self._contours
        if contour.getParent() != self:
            self._setParentDataInContour(contour)
        self._contours.insert(index, contour)
        self._boundsCache = None
        self.dirty = True

    def removeContour(self, contour):
        self._contours.remove(contour)
        self._removeParentDataInContour(contour)
        self._boundsCache = None
        self.dirty = True

    def removeComponent(self, component):
        self._components.remove(component)
        self._removeParentDataInComponent(component)
        self._boundsCache = None
        self.dirty = True

    def removeAnchor(self, anchor):
        self._anchors.remove(anchor)
        self._removeParentDataInAnchor(anchor)
        self.dirty = True

    def contourIndex(self, obj):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> contour = glyph[0]
        >>> glyph.contourIndex(contour)
        0
        >>> contour = glyph[1]
        >>> glyph.contourIndex(contour)
        1
        """
        return self._contours.index(obj)

    def componentIndex(self, obj):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['C']
        >>> component = glyph.components[0]
        >>> glyph.componentIndex(component)
        0
        >>> component = glyph.components[1]
        >>> glyph.componentIndex(component)
        1
        """
        return self._components.index(obj)

    def anchorIndex(self, obj):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> anchor = glyph.anchors[0]
        >>> glyph.anchorIndex(anchor)
        0
        >>> anchor = glyph.anchors[1]
        >>> glyph.anchorIndex(anchor)
        1
        """
        return self._anchors.index(obj)

    def clear(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.clear()
        >>> len(glyph)
        0
        >>> len(glyph.anchors)
        0
        >>> glyph = font['C']
        >>> glyph.clear()
        >>> len(glyph.components)
        0
        """
        self._contours = []
        self._components = []
        self._anchors = []
        self.dirty = True

    def clearContours(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.clearContours()
        >>> len(glyph)
        0
        """
        if self._contours:
            self._contours = []
            self.dirty = True

    def clearComponents(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['C']
        >>> glyph.clearComponents()
        >>> len(glyph.components)
        0
        """
        if self._components:
            self._components = []
            self.dirty = True

    def clearAnchors(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.clearAnchors()
        >>> len(glyph.anchors)
        0
        """
        if self._anchors:
            self._anchors = []
            self.dirty = True

    def move(self, (x, y)):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> xMin, yMin, xMax, yMax = glyph.bounds
        >>> glyph.move((100, 50))
        >>> (xMin+100, yMin+50, xMax+100, yMax+50) == glyph.bounds
        True
        >>> glyph = font['C']
        >>> xMin, yMin, xMax, yMax = glyph.bounds

        #>>> glyph.move((100, 50))
        #>>> (xMin+100, yMin+50, xMax+100, yMax+50) == glyph.bounds
        #True
        """
        oldBounds = self._boundsCache
        for contour in self._contours:
            contour.move((x, y))
        for component in self._components:
            component.move((x, y))
        for anchor in self._anchors:
            anchor.move((x, y))
        if oldBounds:
            xMin, yMin, xMax, yMax = oldBounds
            xMin += x
            yMin += y
            xMax += x
            yMax += y
            self._boundsCache = (xMin, yMin, xMax, yMax)

    def pointInside(self, (x, y), evenOdd=False):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> glyph = font['A']
        >>> glyph.pointInside((100, 100))
        True
        >>> glyph.pointInside((350, 350))
        False
        >>> glyph.pointInside((-100, -100))
        False
        """
        from fontTools.pens.pointInsidePen import PointInsidePen
        pen = PointInsidePen(glyphSet=None, testPoint=(x, y), evenOdd=evenOdd)
        self.draw(pen)
        return pen.getResult()

    def autoContourDirection(self, baseDirectionIsClockwise=False):
        """
        Known problems:
        - speed. This could be sped up by not testing every
          point in overlapping contours, but that would
          result in less accurate results.
        - contours whith points that overlap, but lines
          which intersect with the other contour. consider
          an "A" with the crossbar defined as a rectangle.

        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath('TestContourDirection.ufo'))
        >>> glyph = font['TestContourDirection1']
        >>> for contour in glyph:
        ...     contour.clockwise = True
        >>> glyph.autoContourDirection()
        >>> [contour.clockwise for contour in glyph]
        [False, True, False]
        >>> glyph = font['TestContourDirection2']
        >>> for contour in glyph:
        ...     contour.clockwise = True
        >>> glyph.autoContourDirection()
        >>> [contour.clockwise for contour in glyph]
        [False, False, True]
        >>> glyph = font['TestContourDirection3']
        >>> for contour in glyph:
        ...     contour.clockwise = True
        >>> glyph.autoContourDirection()
        >>> [contour.clockwise for contour in glyph]
        [False, True, True, True, True]
        >>> glyph = font['TestContourDirection4']
        >>> for contour in glyph:
        ...     contour.clockwise = True
        >>> glyph.autoContourDirection()
        >>> [contour.clockwise for contour in glyph]
        [False, False, True]
        """
        baseDirection = baseDirectionIsClockwise
        # if only one contour is present, set
        # the default direction and return
        contourCount = len(self._contours)
        if contourCount < 2:
            for contour in self._contours:
                contour.clockwise = baseDirection
            return
        #
        countIter = xrange(contourCount)
        intersections = {}
        for index1 in countIter:
            for index2 in countIter:
                # don't test the same contour with itself
                if index1 == index2:
                    continue
                # test for intersection of the two contours
                bounds1 = self._contours[index1].bounds
                bounds2 = self._contours[index2].bounds
                intersects, position = arrayTools.sectRect(bounds1, bounds2)
                if intersects:
                    # only flag the contours if they are complete overlaps
                    combinedRect = arrayTools.unionRect(bounds1, bounds2)
                    if combinedRect == bounds1 or combinedRect == bounds2:
                        if index1 not in intersections:
                            intersections[index1] = []
                        intersections[index1].append(index2)
        for index in countIter:
            direction = baseDirection
            contour = self[index]
            intersectingContours = intersections.get(index)
            if intersectingContours:
                for otherContourIndex in intersectingContours:
                    otherContour = self[otherContourIndex]
                    foundPointOutside = False
                    for point in contour:
                        if not point.segmentType:
                            continue
                        pt = (point.x, point.y)
                        if not otherContour.pointInside(pt):
                            foundPointOutside = True
                            break
                    if foundPointOutside:
                        continue
                    direction += 1
            contour.clockwise = direction % 2

    # ---------------
    # Representations
    # ---------------

    def destroyRepresentation(self, name, **kwargs):
        if kwargs:
            key = [name] + sorted(kwargs.items())
            key = tuple(key)
        else:
            key = name
        if key in self._representations:
            del self._representations[key]

    def destroyAllRepresentations(self, notification):
        self._representations = {}

    def getRepresentation(self, name, **kwargs):
        if kwargs:
            key = [name] + sorted(kwargs.items())
            key = tuple(key)
        else:
            key = name
        if key not in self._representations:
            factory = _representationFactories[name]
            representation = factory(self, self.getParent(), **kwargs)
            self._representations[key] = representation
        return self._representations[key]

    # ----
    # Undo
    # ----

    def prepareUndo(self):
        """
        add the current state of the glyph to the undo manager
        """
        raise NotImplementedError

    def assignUndoTitle(self):
        """
        add a title string to the last undo state
        """
        raise NotImplementedError

    def undo(self):
        """
        revert to the previous glyph state
        """
        raise NotImplementedError

    def redo(self):
        """
        undo the last undo
        """
        raise NotImplementedError

    def clearUndoStack(self):
        """
        remove all undoable glyph states
        """
        raise NotImplementedError

    def clearRedoStack(self):
        """
        remove all redoable glyph states
        """
        raise NotImplementedError

    # ----------------------
    # Notification Callbacks
    # ----------------------

    def _outlineContentChanged(self, notification):
        self._boundsCache = None
        self.dirty = True


if __name__ == "__main__":
    import doctest
    doctest.testmod()
