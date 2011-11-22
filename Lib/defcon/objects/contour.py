import weakref
from warnings import warn
from fontTools.misc import bezierTools
from defcon.objects.base import BaseObject
from defcon.tools import bezierMath


class Contour(BaseObject):

    """
    This object represents a contour and it contains a list of points.

    **This object posts the following notifications:**

    ===============================
    Name
    ===============================
    Contour.Changed
    Contour.WindingDirectionChanged
    Contour.PointsChanged
    Contour.IdentifierChanged
    ===============================

    The Contour object has list like behavior. This behavior allows you to interact
    with point data directly. For example, to get a particular point::

        point = contour[0]

    To iterate over all points::

        for point in contour:

    To get the number of points::

        pointCount = len(contour)

    To interact with components or anchors in a similar way,
    use the ``components`` and ``anchors`` attributes.
    """

    changeNotificationName = "Contour.Changed"
    representationFactories = {}

    def __init__(self, pointClass=None):
        super(Contour, self).__init__()
        self._points = []
        self._boundsCache = None
        self._controlPointBoundsCache = None
        self._clockwiseCache = None
        if pointClass is None:
            from point import Point
            pointClass = Point
        self._pointClass = pointClass
        self._identifier = None

    def _destroyBoundsCache(self):
        self._boundsCache = None
        self._controlPointBoundsCache = None

    # ----------
    # Attributes
    # ----------

    # parents

    def _get_font(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.font

    font = property(_get_font, doc="The :class:`Font` that this contour belongs to.")

    def _get_layerSet(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.layerSet

    layerSet = property(_get_layerSet, doc="The :class:`LayerSet` that this contour belongs to.")

    def _get_layer(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.layer

    layer = property(_get_layer, doc="The :class:`Layer` that this contour belongs to.")

    def _get_glyph(self):
        return self.getParent()

    glyph = property(_get_glyph, doc="The :class:`Glyph` that this contour belongs to.")

    def _get_pointClass(self):
        return self._pointClass

    pointClass = property(_get_pointClass, doc="The class used for point.")

    def _get_bounds(self):
        from robofab.pens.boundsPen import BoundsPen
        if self._boundsCache is None:
            pen = BoundsPen(None)
            self.draw(pen)
            self._boundsCache = pen.bounds
        return self._boundsCache

    bounds = property(_get_bounds, doc="The bounds of the contour's outline expressed as a tuple of form (xMin, yMin, xMax, yMax).")

    def _get_controlPointBounds(self):
        from fontTools.pens.boundsPen import ControlBoundsPen
        if self._controlPointBoundsCache is None:
            pen = ControlBoundsPen(None)
            self.draw(pen)
            self._controlPointBoundsCache = pen.bounds
        return self._controlPointBoundsCache

    controlPointBounds = property(_get_controlPointBounds, doc="The control bounds of all points in the contour. This only measures the point positions, it does not measure curves. So, curves without points at the extrema will not be properly measured.")

    def _get_clockwise(self):
        from defcon.pens.clockwiseTestPointPen import ClockwiseTestPointPen
        if self._clockwiseCache is None:
            pen = ClockwiseTestPointPen()
            self.drawPoints(pen)
            self._clockwiseCache = pen.getIsClockwise()
        return self._clockwiseCache

    def _set_clockwise(self, value):
        if self.clockwise != value:
            self.reverse()
            self._clockwiseCache = None

    clockwise = property(_get_clockwise, _set_clockwise, doc="A boolean representing if the contour has a clockwise direction. Setting this posts *Contour.WindingDirectionChanged* and *Contour.Changed* notifications.")

    def _get_open(self):
        if not self._points:
            return True
        return self._points[0].segmentType == 'move'

    open = property(_get_open, doc="A boolean indicating if the contour is open or not.")

    def _get_onCurvePoints(self):
        return [point for point in self._points if point.segmentType]

    onCurvePoints = property(_get_onCurvePoints, doc="A list of all on curve points in the contour.")

    def _get_segments(self):
        if not len(self._points):
            return []
        segments = [[]]
        lastWasOffCurve = False
        for point in self._points:
            segments[-1].append(point)
            if point.segmentType is not None:
                segments.append([])
            lastWasOffCurve = point.segmentType is None
        if len(segments[-1]) == 0:
            del segments[-1]
        if lastWasOffCurve:
            segment = segments.pop(-1)
            assert len(segments[0]) == 1
            segment.append(segments[0][0])
            del segments[0]
            segments.append(segment)
        elif segments[0][-1].segmentType != "move":
            segment = segments.pop(0)
            segments.append(segment)
        return segments

    segments = property(_get_segments, doc="A list of all points in the contour organized into segments.")

    # -------
    # Methods
    # -------

    def __len__(self):
        return len(self._points)

    def __getitem__(self, index):
        if index > len(self._points):
            raise IndexError
        return self._points[index]

    def __iter__(self):
        pointCount = len(self)
        index = 0
        while index < pointCount:
            point = self[index]
            yield point
            index += 1

    def clear(self):
        """
        Clear the contents of the contour.

        This posts *Contour.PointsChanged* and *Contour.Changed* notifications.
        """
        self._clear()

    def _clear(self, postNotification=True):
        # clear the internal storage
        self._points = []
        # reset the clockwise cache
        self._clockwiseCache = None
        # post a dirty notification
        if postNotification:
            self.postNotification("Contour.PointsChanged")
            self.dirty = True

    def appendPoint(self, point):
        """
        Append **point** to the glyph. The point must be a defcon
        :class:`Point` object or a subclass of that object. An error
        will be raised if the point's identifier conflicts with any of
        the identifiers within the glyph.

        This will post *Contour.PointsChanged* and *Contour.Changed* notifications.
        """
        assert point not in self._points
        self.insertPoint(len(self._points), point)

    def insertPoint(self, index, point):
        """
        Insert **point** into the contour at index. The point
        must be a defcon :class:`Point` object or a subclass
        of that object. An error will be raised if the points's
        identifier conflicts with any of the identifiers within
        the glyph.

        This will post *Contour.PointsChanged* and *Contour.Changed* notifications.
        """
        assert point not in self._points
        if point.identifier is not None:
            identifiers = self.identifiers
            assert point.identifier not in identifiers
            if point.identifier is not None:
                identifiers.add(point.identifier)
        self._points.insert(index, point)
        self._destroyBoundsCache()
        self._clockwiseCache = None
        self.postNotification("Contour.PointsChanged")
        self.dirty = True

    def reverse(self):
        """
        Reverse the direction of the contour.

        This will post *Contour.WindingDirectionChanged*,
        *Contour.PointsChanged* and *Contour.Changed* notifications.
        """
        from robofab.pens.reverseContourPointPen import ReverseContourPointPen
        oldDirection = self.clockwise
        # put the current points in another contour
        otherContour = self.__class__(self._pointClass)
        # draw the points in this contour through
        # the reversing pen.
        reversePen = ReverseContourPointPen(otherContour)
        self.drawPoints(reversePen)
        # clear the points in this contour
        # and copy the points from the other
        # contour to this contour.
        self._clear(postNotification=False)
        self._points = list(otherContour._points)
        # post a notification
        self.postNotification("Contour.WindingDirectionChanged", data=dict(oldValue=oldDirection, newValue=self.clockwise))
        self.postNotification("Contour.PointsChanged")
        self.dirty = True

    def move(self, (x, y)):
        """
        Move all points in the contour by **(x, y)**.

        This will post *Contour.PointsChanged* and *Contour.Changed* notifications.
        """
        for point in self._points:
            point.move((x, y))
        # update the bounds cache
        if self._boundsCache:
            xMin, yMin, xMax, yMax = self._boundsCache
            xMin += x
            yMin += y
            xMax += x
            yMax += y
            self._boundsCache = (xMin, yMin, xMax, yMax)
        if self._controlPointBoundsCache:
            xMin, yMin, xMax, yMax = self._controlPointBoundsCache
            xMin += x
            yMin += y
            xMax += x
            yMax += y
            self._controlPointBoundsCache = (xMin, yMin, xMax, yMax)
        self.postNotification("Contour.PointsChanged")
        self.dirty = True

    def pointInside(self, (x, y), evenOdd=False):
        """
        Returns a boolean indicating if **(x, y)** is in the
        "black" area of the contour.
        """
        from fontTools.pens.pointInsidePen import PointInsidePen
        pen = PointInsidePen(glyphSet=None, testPoint=(x, y), evenOdd=evenOdd)
        self.draw(pen)
        return pen.getResult()

    def index(self, point):
        """
        Get the index for **point**.
        """
        return self._points.index(point)

    def setStartPoint(self, index):
        """
        Set the point at **index** as the first point in the contour.
        This point must be an on-curve point.

        This will post *Contour.PointsChanged* and *Contour.Changed* notifications.
        """
        onCurvePoints = self.onCurvePoints
        if len(onCurvePoints) < 2:
            return
        if self.open:
            return
        point = self._points[index]
        assert point.segmentType is not None, "index must represent an on curve point"
        before = self._points[:index]
        self._points = self._points[index:] + before
        self.postNotification("Contour.PointsChanged")
        self.dirty = True

    def positionForProspectivePointInsertionAtSegmentAndT(self, segmentIndex, t):
        """
        Get the precise coordinates and a boolean indicating
        if the point will be smooth for the given **segmentIndex**
        and **t**.
        """
        return self._splitAndInsertAtSegmentAndT(segmentIndex, t, False)

    def splitAndInsertPointAtSegmentAndT(self, segmentIndex, t):
        """
        Insert a point into the contour for the given
        **segmentIndex** and **t**.

        This posts a *Contour.Changed* notification.
        """
        self._splitAndInsertAtSegmentAndT(segmentIndex, t, True)

    def _splitAndInsertAtSegmentAndT(self, segmentIndex, t, insert):
        segments = self.segments
        segment = segments[segmentIndex]
        segment.insert(0, segments[segmentIndex-1][-1])
        firstPoint = segment[0]
        lastPoint = segment[-1]
        segmentType = lastPoint.segmentType
        segment = [(point.x, point.y) for point in segment]
        if segmentType == "line":
            (x1, y1), (x2, y2) = segment
            x = x1 + (x2 - x1) * t
            y = y1 + (y2 - y1) * t
            pointsToInsert = [((x, y), "line", False)]
            insertionPoint =  (x, y)
            pointWillBeSmooth = False
        elif segmentType == "curve":
            pt1, pt2, pt3, pt4 = segment
            (pt1, pt2, pt3, pt4), (pt5, pt6, pt7, pt8) = bezierTools.splitCubicAtT(pt1, pt2, pt3, pt4, t)
            pointsToInsert = [(pt2, None, False), (pt3, None, False), (pt4, "curve", True), (pt6, None, False), (pt7, None, False)]
            insertionPoint = tuple(pt4)
            pointWillBeSmooth = True
        else:
            # XXX could be a quad. in that case, we could handle it.
            raise NotImplementedError("unknown segment type: %s" % segmentType)
        if insert:
            firstPointIndex = self._points.index(firstPoint)
            lastPointIndex = self._points.index(lastPoint)
            firstPoints = self._points[:firstPointIndex + 1]
            if firstPointIndex == len(self._points) - 1:
                firstPoints = firstPoints[lastPointIndex:]
                lastPoints = []
            elif lastPointIndex == 0:
                lastPoints = []
            else:
                lastPoints = self._points[lastPointIndex:]
            newPoints = [self._pointClass(pos, segmentType=segmentType, smooth=smooth) for pos, segmentType, smooth in pointsToInsert]
            self._points = firstPoints + newPoints + lastPoints
            self.dirty = True
        return insertionPoint, pointWillBeSmooth

    def removeSegment(self, segmentIndex, preserveCurve=False):
        """
        Remove the segment at **segmentIndex**. If
        **preserveCurve** is True, the contour will
        try to preserve the overall curve shape.
        """
        segments = self.segments
        nextIndex = segmentIndex + 1
        if nextIndex == len(segments):
            nextIndex = 0
        previousIndex = segmentIndex - 1
        if previousIndex < 0:
            previousIndex = len(segments) + previousIndex
        nextSegment = segments[nextIndex]
        segment = segments[segmentIndex]
        previousSegment = segments[previousIndex]
        # if preserveCurve is off
        # or if all are lines, handle it
        if not preserveCurve or (previousSegment[-1].segmentType == "line"\
            and segment[-1].segmentType == "line"\
            and nextSegment[-1].segmentType == "line"):
            for point in segment:
                self._points.remove(point)
        # if have a curve, do the preservation
        else:
            # gather the needed points
            previousOnCurveX = previousSegment[-1].x
            previousOnCurveY = previousSegment[-1].y
            onCurveX = segment[-1].x
            onCurveY = segment[-1].y
            nextOnCurveX = nextSegment[-1].x
            nextOnCurveY = nextSegment[-1].y
            if segment[-1].segmentType == "curve":
                offCurve1X = segment[0].x
                offCurve1Y = segment[0].y
                offCurve2X = segment[-2].x
                offCurve2Y = segment[-2].y
            elif segment[-1].segmentType == "line":
                offCurve1X = previousOnCurveX
                offCurve1Y = previousOnCurveY
                offCurve2X = onCurveX
                offCurve2Y = onCurveY
            else:
                # XXX could be a quad. in that case, we can't handle it.
                raise NotImplementedError("unknown segment type: %s" % segment[-1].segmentType)
            if nextSegment[-1].segmentType == "curve":
                nextOffCurve1X = nextSegment[0].x
                nextOffCurve1Y = nextSegment[0].y
                nextOffCurve2X = nextSegment[-2].x
                nextOffCurve2Y = nextSegment[-2].y
            elif nextSegment[-1].segmentType == "line":
                nextOffCurve1X = onCurveX
                nextOffCurve1Y = onCurveY
                nextOffCurve2X = nextOnCurveX
                nextOffCurve2Y = nextOnCurveY
            else:
                # XXX could be a quad. in that case, we can't handle it.
                raise NotImplementedError("unknown segment type: %s" % nextSegment[-1].segmentType)
            # now do the math
            result = bezierMath.joinSegments((previousOnCurveX, previousOnCurveY),
                (offCurve1X, offCurve1Y), (offCurve2X, offCurve2Y), (onCurveX, onCurveY),
                (nextOffCurve1X, nextOffCurve1Y), (nextOffCurve2X, nextOffCurve2Y), (nextOnCurveX, nextOnCurveY))
            # remove the segment
            for point in segment:
                self._points.remove(point)
            # if the next segment type isn't a curve, make it one
            if not nextSegment[-1].segmentType == "curve":
                nextSegment[-1].segmentType = "curve"
                pointIndex = self._points.index(nextSegment[-1])
                newPoints = [self._pointClass((result[0][0], result[0][1])), self._pointClass((result[1][0], result[1][1]))]
                if pointIndex == 0:
                    self._points.extend(newPoints)
                else:
                    self._points = self._points[:pointIndex] + newPoints + self._points[pointIndex:]
            # otherwise, set the point positions
            else:
                nextSegment[0].x = result[0][0]
                nextSegment[0].y = result[0][1]
                nextSegment[1].x = result[1][0]
                nextSegment[1].y = result[1][1]
        # mark the contour as dirty
        self._destroyBoundsCache()
        self.dirty = True

    # -----------
    # Pen methods
    # -----------

    def beginPath(self):
        """
        Standard point pen *beginPath* method.
        This should not be used externally.
        """
        pass

    def endPath(self):
        """
        Standard point pen *endPath* method.
        This should not be used externally.
        """
        pass

    def addPoint(self, (x, y), segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        """
        Standard point pen *addPoint* method.
        This should not be used externally.
        """
        point = self._pointClass((x, y), segmentType=segmentType, smooth=smooth, name=name, identifier=identifier)
        self.insertPoint(len(self._points), point)

    def draw(self, pen):
        """
        Draw the contour with **pen**.
        """
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """
        Draw the contour with **pointPen**.
        """
        try:
            pointPen.beginPath(identifier=self.identifier)
        except TypeError:
            pointPen.beginPath()
            warn("The beginPath method needs an identifier kwarg. The contour's identifier value has been discarded.", DeprecationWarning)
        for point in self._points:
            try:
                pointPen.addPoint((point.x, point.y), segmentType=point.segmentType, smooth=point.smooth, name=point.name, identifier=point.identifier)
            except TypeError:
                pointPen.addPoint((point.x, point.y), segmentType=point.segmentType, smooth=point.smooth, name=point.name)
                warn("The addPoint method needs an identifier kwarg. The point's identifier value has been discarded.", DeprecationWarning)
        pointPen.endPath()

    # ----------
    # Identifier
    # ----------

    def _get_identifiers(self):
        identifiers = None
        glyph = self.glyph
        if glyph is not None:
            identifiers = glyph.identifiers
        if identifiers is None:
            identifiers = set()
        return identifiers

    identifiers = property(_get_identifiers, doc="Set of identifiers for the glyph that this contour belongs to. This is primarily for internal use.")

    def _get_identifier(self):
        return self._identifier

    def _set_identifier(self, value):
        oldIdentifier = self.identifier
        if value == oldIdentifier:
            return
        # don't allow a duplicate
        identifiers = self.identifiers
        assert value not in identifiers
        # free the old identifier
        if oldIdentifier in identifiers:
            identifiers.remove(oldIdentifier)
        # store
        self._identifier = value
        if value is not None:
            identifiers.add(value)
        # post notifications
        self.postNotification("Contour.IdentifierChanged", data=dict(oldValue=oldIdentifier, newValue=value))
        self.dirty = True

    identifier = property(_get_identifier, _set_identifier, doc="The identifier. Setting this will post *Contour.IdentifierChanged* and *Contour.Changed* notifications.")

    def generateIdentifier(self):
        """
        Create a new, unique identifier for and assign it to the contour.
        This will post *Contour.IdentifierChanged* and *Contour.Changed* notifications.
        """
        identifier = makeRandomIdentifier(existing=self.identifiers)
        self.identifier = identifier

    def generateIdentifierForPoint(self, point):
        """
        Create a new, unique identifier for and assign it to the contour.
        This will post *Contour.IdentifierChanged* and *Contour.Changed* notifications.
        """
        identifier = makeRandomIdentifier(existing=self.identifiers)
        point.identifier = identifier
        self.dirty = True

# -----
# Tests
# -----

def _testIdentifier():
    """
    >>> from defcon import Glyph
    >>> glyph = Glyph()
    >>> contour = Contour()
    >>> glyph.appendContour(contour)
    >>> contour.identifier = "contour 1"
    >>> contour.identifier
    'contour 1'
    >>> list(sorted(glyph.identifiers))
    ['contour 1']
    >>> contour = Contour()
    >>> glyph.appendContour(contour)
    >>> contour.identifier = "contour 1"
    Traceback (most recent call last):
        ...
    AssertionError
    >>> contour.identifier = "contour 2"
    >>> list(sorted(glyph.identifiers))
    ['contour 1', 'contour 2']
    >>> contour.identifier = "not contour 2 anymore"
    >>> contour.identifier
    'not contour 2 anymore'
    >>> list(sorted(glyph.identifiers))
    ['contour 1', 'not contour 2 anymore']
    >>> contour.identifier = None
    >>> contour.identifier
    >>> list(sorted(glyph.identifiers))
    ['contour 1']
    """

def _testBounds():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.bounds
    (0, 0, 700, 700)
    """

def _testControlPointBounds():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.controlPointBounds
    (0, 0, 700, 700)
    """

def _testClockwise():
    """
    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.clockwise
    False
    >>> contour = font['A'][1]
    >>> contour.clockwise
    True
    >>> contour._clockwiseCache = None
    >>> contour.clockwise = False
    >>> contour.clockwise
    False
    >>> contour._clockwiseCache = None
    >>> contour.clockwise = True
    >>> contour.clockwise
    True

    # set
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.clockwise = False
    >>> contour.clockwise
    False
    >>> contour._clockwiseCache = None
    >>> contour.clockwise = True
    >>> contour.clockwise
    True
    """

def _testOpen():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath('TestOpenContour.ufo'))
    >>> glyph = font['A']
    >>> glyph[0].open
    True
    >>> glyph[1].open
    False
    >>> glyph[2].open
    True
    >>> glyph[3].open
    False
    """

def _testOnCurvePoints():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> contour = glyph[0]
    >>> len(contour.onCurvePoints)
    4
    >>> [(point.x, point.y) for point in contour.onCurvePoints]
    [(0, 0), (700, 0), (700, 700), (0, 700)]
    
    >>> glyph = font['B']
    >>> contour = glyph[0]
    >>> len(contour.onCurvePoints)
    4
    >>> [(point.x, point.y) for point in contour.onCurvePoints]
    [(0, 350), (350, 0), (700, 350), (350, 700)]
    """

def _testSegments():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> def simpleSegment(segment):
    ...     return [(i.x, i.y, i.segmentType) for i in segment]
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> contour = glyph[0]
    >>> [simpleSegment(segment) for segment in contour.segments]
    [[(700, 0, 'line')], [(700, 700, 'line')], [(0, 700, 'line')], [(0, 0, 'line')]]
    >>> glyph = font['B']
    >>> contour = glyph[0]
    >>> [simpleSegment(segment) for segment in contour.segments]
    [[(0, 157, None), (157, 0, None), (350, 0, 'curve')], [(543, 0, None), (700, 157, None), (700, 350, 'curve')], [(700, 543, None), (543, 700, None), (350, 700, 'curve')], [(157, 700, None), (0, 543, None), (0, 350, 'curve')]]
    """

def _testLen():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> len(contour)
    4
    >>> contour = font['B'][0]
    >>> len(contour)
    12
    """

def _testIter():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> [(point.x, point.y) for point in contour]
    [(0, 0), (700, 0), (700, 700), (0, 700)]
    """

def _testReverse():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.reverse()
    >>> [(point.x, point.y) for point in contour._points]
    [(0, 0), (0, 700), (700, 700), (700, 0)]
    >>> contour.reverse()
    >>> [(point.x, point.y) for point in contour._points]
    [(0, 0), (700, 0), (700, 700), (0, 700)]
    """

def _testMove():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.move((100, 100))
    >>> contour.bounds
    (100, 100, 800, 800)
    >>> contour.dirty = True
    """

def _testPointInside():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.pointInside((100, 100))
    True
    >>> contour.pointInside((0, 0))
    False
    >>> contour.pointInside((-100, -100))
    False
    """

def _testIndex():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['B'][0]
    >>> 2 == contour.index(contour[2])
    True
    """

def _testSetStartPoint():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['B'][0]
    >>> start = [(point.segmentType, point.x, point.y) for point in contour]
    >>> contour.setStartPoint(6)
    >>> contour.dirty
    True
    >>> contour.setStartPoint(6)
    >>> end = [(point.segmentType, point.x, point.y) for point in contour]
    >>> start == end
    True
    >>> contour = font['A'][0]
    >>> start = [(point.segmentType, point.x, point.y) for point in contour]
    >>> contour.setStartPoint(2)
    >>> contour.setStartPoint(2)
    >>> end = [(point.segmentType, point.x, point.y) for point in contour]
    >>> start == end
    True
    >>> contour = font['B'][0]
    >>> start = [(point.segmentType, point.x, point.y) for point in contour]
    >>> contour.setStartPoint(3)
    >>> contour.setStartPoint(9)
    >>> end = [(point.segmentType, point.x, point.y) for point in contour]
    >>> start == end
    True
    """

def _testPositionForProspectivePointInsertionAtSegmentAndT():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.positionForProspectivePointInsertionAtSegmentAndT(0, .5)
    ((350.0, 0.0), False)
    >>> contour = font['B'][0]
    >>> contour.positionForProspectivePointInsertionAtSegmentAndT(0, .5)
    ((102.625, 102.625), True)
    >>> contour = font['B'][1]
    >>> contour.positionForProspectivePointInsertionAtSegmentAndT(0, .5)
    ((226.125, 473.5), True)
    """

def _testSplitAndInsertPointAtSegmentAndT():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> contour = font['A'][0]
    >>> contour.splitAndInsertPointAtSegmentAndT(0, .5)
    >>> [(point.x, point.y, point.segmentType) for point in contour]
    [(0, 0, 'line'), (350.0, 0.0, 'line'), (700, 0, 'line'), (700, 700, 'line'), (0, 700, 'line')]
    >>> contour = font['B'][0]
    >>> contour.splitAndInsertPointAtSegmentAndT(0, .5)
    >>> [(point.x, point.y, point.segmentType) for point in contour]
    [(0, 350, 'curve'), (0.0, 253.5, None), (39.25, 166.0, None), (102.625, 102.625, 'curve'), (166.0, 39.25, None), (253.5, 0.0, None), (350, 0, 'curve'), (543, 0, None), (700, 157, None), (700, 350, 'curve'), (700, 543, None), (543, 700, None), (350, 700, 'curve'), (157, 700, None), (0, 543, None)]
    """

def _testRemoveSegment():
    """
    >>> print "need removeSegment tests!"
    """


if __name__ == "__main__":
    import doctest
    doctest.testmod()
