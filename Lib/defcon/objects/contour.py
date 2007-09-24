from fontTools.misc import bezierTools
from defcon.objects.base import BaseObject
from defcon.objects.point import Point


class Contour(BaseObject):

    _notificationName = "Contour.Changed"

    def __init__(self, dispatcher=None):
        super(Contour, self).__init__(dispatcher)
        self._points = []
        self._boundsCache = None
        self._clockwiseCache = None

    #-----------
    # Attributes
    #-----------

    def _get_bounds(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> contour = font['A'][0]
        >>> contour.bounds
        (0, 0, 700, 700)
        """
        from robofab.pens.boundsPen import BoundsPen
        if self._boundsCache is None:
            pen = BoundsPen(None)
            self.draw(pen)
            self._boundsCache = pen.bounds
        return self._boundsCache

    bounds = property(_get_bounds)

    def _get_clockwise(self):
        """
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
        """
        from defcon.pens.clockwiseTestPointPen import ClockwiseTestPointPen
        if self._clockwiseCache is None:
            pen = ClockwiseTestPointPen()
            self.drawPoints(pen)
            self._clockwiseCache = pen.getIsClockwise()
        return self._clockwiseCache

    def _set_clockwise(self, value):
        """
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
        if self.clockwise != value:
            self.reverse()
            self._clockwiseCache = None

    clockwise = property(_get_clockwise, _set_clockwise)

    def _get_open(self):
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
        if not self._points:
            return True
        return self._points[0].segmentType == 'move'

    open = property(_get_open)

    def _get_onCurvePoints(self):
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
        return [point for point in self._points if point.segmentType]

    onCurvePoints = property(_get_onCurvePoints)

    def _get_segments(self):
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

    segments = property(_get_segments)

    #--------
    # Methods
    #--------

    def __len__(self):
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
        return len(self._points)

    def __getitem__(self, index):
        if index > len(self._points):
            raise IndexError
        return self._points[index]

    def reverse(self):
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
        from robofab.pens.reverseContourPointPen import ReverseContourPointPen
        # put the current points in another contour
        otherContour = Contour()
        # draw the points in this contour through
        # the reversing pen.
        reversePen = ReverseContourPointPen(otherContour)
        self.drawPoints(reversePen)
        # clear the points in this contour
        # and copy the points from the other
        # contour to this contour.
        self._points = list(otherContour._points)
        # reset the clockwise cache
        self._clockwiseCache = None
        self.dirty = True

    def move(self, (x, y)):
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
        self.dirty = True

    def pointInside(self, (x, y), evenOdd=False):
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
        from fontTools.pens.pointInsidePen import PointInsidePen
        pen = PointInsidePen(glyphSet=None, testPoint=(x, y), evenOdd=evenOdd)
        self.draw(pen)
        return pen.getResult()

    def index(self, point):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> contour = font['B'][0]
        >>> 2 == contour.index(contour[2])
        True
        """
        return self._points.index(point)

    def setStartPoint(self, index):
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
        onCurvePoints = self.onCurvePoints
        if len(onCurvePoints) < 2:
            return
        if self.open:
            return
        point = self._points[index]
        assert point.segmentType is not None, 'index must represent an on curve point'
        before = self._points[:index]
        self._points = self._points[index:] + before
        self.dirty = True

    #------------
    # Pen methods
    #------------

    def beginPath(self):
        pass

    def endPath(self):
        pass

    def addPoint(self, (x, y), segmentType=None, smooth=False, name=None):
        point = Point((x, y), segmentType=segmentType, smooth=smooth, name=name)
        self._points.append(point)
        self._boundsCache = None
        self._clockwiseCache = None
        self.dirty = True

    def draw(self, pen):
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        pointPen.beginPath()
        for point in self._points:
            pointPen.addPoint((point.x, point.y), segmentType=point.segmentType, smooth=point.smooth, name=point.name)
        pointPen.endPath()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
