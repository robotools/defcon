import math
from fontTools.pens.basePen import BasePen
from robofab.pens.reverseContourPointPen import ReverseContourPointPen
from robofab.pens.adapterPens import PointToSegmentPen

"""
notes:
- the flattened segments *must* be cyclical.
  if they aren't, matching is almost impossible.


optimization ideas:
- use the point pen protocol instead of the pen protocol.
  this would make the inetrnal tracking harder, but that
  could be solved by grouping the points into segments
  internally. using points this way would make it easier
  to reverse the direction (there would be no need for
  the reversal point pen or the adapter pen). this could
  help solve another problem down the road if more poiont
  attributes need to be retained.
- the flattening of the output segment in the full contour
  matching is probably expensive.
- there should be a way to flag an input contour as
  entirely used so that it isn't tried and tried and
  tried for segment matches.

test cases:
- untouched contour: make clockwise and counter-clockwise tests
  of the same contour
"""


# -------
# Objects
# -------

# Input

class InputContour(object):

    def __init__(self, contour, scale=1):
        self.clockwise = contour.clockwise
        self.used = False
        # draw normal
        pen = InputContourPen(scale=scale)
        contour.draw(pen)
        if self.clockwise:
            self.clockwiseSegments = pen.segments
        else:
            self.counterClockwiseSegments = pen.segments
        # draw reversed
        pen = InputContourPen(scale=scale)
        self._drawReversed(contour, pen)
        if self.clockwise:
            self.counterClockwiseSegments = pen.segments
        else:
            self.clockwiseSegments = pen.segments

    def _drawReversed(self, contour, pen):
        adapterPen = PointToSegmentPen(pen, outputImpliedClosingLine=True)
        reversePointPen = ReverseContourPointPen(adapterPen)
        contour.drawPoints(reversePointPen)

    # ----------
    # Attributes
    # ----------

    # the original direction in flat segments

    def _get_originalFlat(self):
        if self.clockwise:
            return self.clockwiseFlat
        else:
            return self.counterClockwiseFlat

    originalFlat = property(_get_originalFlat)

    # the clockwise direction in flat segments

    def _get_clockwiseFlat(self):
        flat = []
        segments = self.clockwiseSegments
        for segment in segments:
            flat += segment.flat
        return flat

    clockwiseFlat = property(_get_clockwiseFlat)

    # the counter-clockwise direction in flat segments

    def _get_counterClockwiseFlat(self):
        flat = []
        segments = self.counterClockwiseSegments
        for segment in segments:
            flat += segment.flat
        return flat

    counterClockwiseFlat = property(_get_counterClockwiseFlat)


class InputSegment(object):

    def __init__(self, segmentType=None, points=None, flat=None):
        self.segmentType = segmentType
        if points is None:
            points = []
        self.points = points
        if flat is None:
            flat = []
        self.flat = flat
        self.used = False


# Output

class OutputContour(object):

    def __init__(self, pointList, scale):
        self.scale = scale
        self.clockwise = getIsClockwise(pointList)
        if pointList[0] == pointList[-1]:
            del pointList[-1]
        self.segments = [OutputSegment(segmentType="flat", points=[tuple(point)]) for point in pointList]

    def _scalePoint(self, point):
        x, y = point
        x = x * self.scale
        if int(x) == x:
            x = int(x)
        y = y * self.scale
        if int(y) == y:
            y = int(y)
        return x, y

    # ----------
    # Attributes
    # ----------

    def _get_final(self):
        # XXX this could be optimized:
        # store a fixed value after teh contour is finalized
        # don't do the dymanic searching if that flag is set to True
        for segment in self.segments:
            if not segment.final:
                return False
        return True

    final = property(_get_final)

    # --------------------------
    # Re-Curve and Curve Fitting
    # --------------------------

    def reCurveFromEntireInputContour(self, inputContour):
        if self.clockwise:
            inputFlat = inputContour.clockwiseFlat
        else:
            inputFlat = inputContour.counterClockwiseFlat
        outputFlat = []
        for segment in self.segments:
            # XXX this could be expensive
            assert segment.segmentType == "flat"
            outputFlat += segment.points
        # test lengths
        haveMatch = False
        if len(inputFlat) == len(outputFlat):
            if inputFlat == outputFlat:
                haveMatch = True
            else:
                inputStart = inputFlat[0]
                if inputStart in outputFlat:
                    # there should be only one occurance of the point
                    # but handle it just in case
                    if outputFlat.count(inputStart) > 1:
                        startIndexes = [index for index, point in enumerate(outputFlat) if point == inputStart]
                    else:
                        startIndexes = [outputFlat.index(inputStart)]
                    # slice and dice to test possible orders
                    for startIndex in startIndexes:
                        test = outputFlat[startIndex:] + outputFlat[:startIndex]
                        if inputFlat == test:
                            haveMatch = True
                            break
        if haveMatch:
            # clear out the flat points
            self.segments = []
            # replace with the appropriate points from the input
            if self.clockwise:
                inputSegments = inputContour.clockwiseSegments
            else:
                inputSegments = inputContour.counterClockwiseSegments
            for inputSegment in inputSegments:
                self.segments.append(
                    OutputSegment(
                        segmentType=inputSegment.segmentType,
                        points=list(inputSegment.points),
                        final=True
                    )
                )
                inputSegment.used = True
            # reset the direction of the final contour
            self.clockwise = inputContour.clockwise
            return True
        return False

    def reCurveFromInputContourSegments(self, inputContour):
        # match individual segments
        if self.clockwise:
            inputSegments = inputContour.clockwiseSegments
        else:
            inputSegments = inputContour.counterClockwiseSegments
        for inputSegment in inputSegments:
            # skip used
            if inputSegment.used:
                continue
            # skip if the input contains more points than the entire output contour
            if len(inputSegment.flat) > len(self.segments):
                continue
            # skip if the input end is not in the contour
            inputSegmentLastPoint = inputSegment.flat[-1]
            outputFlat = [segment.points[-1] for segment in self.segments]
            if inputSegmentLastPoint not in outputFlat:
                continue
            # work through all output segments
            for outputSegmentIndex, outputSegment in enumerate(self.segments):
                # skip finalized
                if outputSegment.final:
                    continue
                # skip if the output point doesn't match the input end
                if outputSegment.points[-1] != inputSegmentLastPoint:
                    continue
                # make a set of ranges for slicing the output into a testable list of points
                inputLength = len(inputSegment.flat)
                outputRanges = []
                outputSegmentIndex += 1
                if outputSegmentIndex - inputLength < 0:
                    r1 = (len(self.segments) + outputSegmentIndex - inputLength, len(self.segments))
                    outputRanges.append(r1)
                    r2 = (0, outputSegmentIndex)
                    outputRanges.append(r2)
                else:
                    outputRanges.append((outputSegmentIndex - inputLength, outputSegmentIndex))
                # gather the output segments
                testableOutputSegments = []
                for start, end in outputRanges:
                    testableOutputSegments += self.segments[start:end]
                # create a list of points
                test = []
                for s in testableOutputSegments:
                    # stop if a segment is final
                    if s.final:
                        test = None
                        break
                    test.append(s.points[-1])
                if test == inputSegment.flat:
                    # insert new segment
                    newSegment = OutputSegment(
                        segmentType=inputSegment.segmentType,
                        points=list(inputSegment.points),
                        final=True
                    )
                    self.segments.insert(outputSegmentIndex, newSegment)
                    # remove old segments
                    # XXX this is sloppy
                    for start, end in outputRanges:
                        if start > outputSegmentIndex:
                            start += 1
                            end += 1
                        del self.segments[start:end]
                    # flag the original as used
                    inputSegment.used = True
                    break
        # ? match line start points (to prevent curve fit in shortened line)
        return False

    def curveFit(self):
        # XXX convert all of the remaining segments to lines
        for index, segment in enumerate(self.segments):
            if segment.segmentType != "flat":
                continue
            segment.segmentType = "line"
            segment.points = [self._scalePoint(point) for point in segment.points]

    # ----
    # Draw
    # ----

    def draw(self, pen):
        # imply the move
        pen.moveTo(self.segments[-1].points[-1])
        # draw the rest
        for segment in self.segments:
            instruction = segment.segmentType
            points = segment.points
            if instruction == "line":
                pen.lineTo(points[0])
            elif instruction == "curve":
                pen.curveTo(*points)
            elif instruction == "qcurve":
                pen.qCurveTo(*points)
        pen.closePath()


class OutputSegment(object):

    def __init__(self, segmentType=None, points=None, final=False):
        self.segmentType = segmentType
        if points is None:
            points = []
        self.points = points
        self.final = final


# taken from defcon.pens.clockwiseTestPointPen
# fork, fork, fork. sigh.
def getIsClockwise(points):
    import math
    # overlapping moves can give false results, so filter them out
    if points[0] == points[-1]:
        del points[-1]
    angles = []
    pointCount = len(points)
    for index1 in xrange(pointCount):
        index2 = (index1 + 1) % pointCount
        x1, y1 = points[index1]
        x2, y2 = points[index2]
        angles.append(math.atan2(y2-y1, x2-x1))
    total = 0
    pi = math.pi
    pi2 = pi * 2
    for index1 in xrange(pointCount):
        index2 = (index1 + 1) % pointCount
        d = ((angles[index2] - angles[index1] + pi) % pi2) - pi
        total += d
    return total < 0



# ----------------
# Curve Flattening
# ----------------

"""
The curve flattening code was forked and modified from RoboFab's FilterPen.
That code was written by Erik van Blokland.
"""

class InputContourPen(BasePen):

    def __init__(self, scale=1, approximateSegmentLength=5):
        BasePen.__init__(self, glyphSet=None)
        self._scale = scale
        self._approximateSegmentLength = approximateSegmentLength
        self._qCurveConversion = None
        # publicly accessible attributes
        self.segments = []

    def _prepFlatPoint(self, pt):
        x, y = pt
        x = x * self._scale
        y = y * self._scale
        x = int(round(x))
        y = int(round(y))
        return (x, y)

    def _moveTo(self, pt):
        assert not self.segments
        segment = InputSegment(
            segmentType="move",
            points=[pt],
            flat=[self._prepFlatPoint(pt)]
        )
        self.segments.append(segment)

    def _lineTo(self, pt):
        currentPoint = self.segments[-1].points[-1]
        if pt == currentPoint:
            return
        segment = InputSegment(
            segmentType="line",
            points=[pt],
            flat=[self._prepFlatPoint(pt)]
        )
        self.segments.append(segment)

    def _curveToOne(self, pt1, pt2, pt3):
        currentPoint = self.segments[-1].points[-1]
        # a false curve
        falseCurve = (pt1 == currentPoint) and (pt2 == pt3)
        if falseCurve:
            self.lineTo(pt3)
            return
        # no possible steps
        est = _estimateCubicCurveLength(currentPoint, pt1, pt2, pt3) / self._approximateSegmentLength
        maxSteps = int(round(est))
        if maxSteps < 1:
            self.lineTo(pt3)
            return
        # a usable curve
        if self._qCurveConversion:
            segment = InputSegment(
                segmentType="qcurve",
                points=self._qCurveConversion
            )
        else:
            segment = InputSegment(
                segmentType="curve",
                points=[pt1, pt2, pt3]
            )
        self.segments.append(segment)
        flattened = segment.flat
        step = 1.0 / maxSteps
        factors = range(0, maxSteps + 1)
        for i in factors[1:]:
            pt = _getCubicPoint(i * step, currentPoint, pt1, pt2, pt3)
            flattened.append(self._prepFlatPoint(pt))

    def _qCurveToOne(self, pt1, pt2):
        self._qCurveConversion = [pt1, pt2]
        BasePen._qCurveToOne(pt1, pt2)
        self._qCurveConversion = None

    def _closePath(self):
        firstPoint = self.segments[0].points[-1]
        lastPoint = self.segments[-1].points[-1]
        if firstPoint == lastPoint:
            assert self.segments[0].segmentType == "move"
            del self.segments[0]
        elif self.segments[0].segmentType == "move":
            self.segments[0].segmentType = "line"

    def _endPath(self):
        raise NotImplementedError

    def addComponent(self, glyphName, transformation):
        raise NotImplementedError


def _intPoint(pt):
    return int(round(pt[0])), int(round(pt[1]))

def distance(pt1, pt2):
    return math.sqrt((pt1[0] - pt2[0]) ** 2 + (pt1[1] - pt2[1]) ** 2)

def _estimateCubicCurveLength(pt0, pt1, pt2, pt3, precision=10):
    """
    Estimate the length of this curve by iterating
    through it and averaging the length of the flat bits.
    """
    points = []
    length = 0
    step = 1.0 / precision
    factors = range(0, precision + 1)
    for i in factors:
        points.append(_getCubicPoint(i * step, pt0, pt1, pt2, pt3))
    for i in range(len(points) - 1):
        pta = points[i]
        ptb = points[i + 1]
        length += distance(pta, ptb)
    return length

def _mid((x0, y0), (x1, y1)):
    """
    (Point, Point) -> Point
    Return the point that lies in between the two input points.
    """
    return 0.5 * (x0 + x1), 0.5 * (y0 + y1)

def _getCubicPoint(t, pt0, pt1, pt2, pt3):
    if t == 0:
        return pt0
    if t == 1:
        return pt3
    if t == 0.5:
        a = _mid(pt0, pt1)
        b = _mid(pt1, pt2)
        c = _mid(pt2, pt3)
        d = _mid(a, b)
        e = _mid(b, c)
        return _mid(d, e)
    else:
        cx = (pt1[0] - pt0[0]) * 3
        cy = (pt1[1] - pt0[1]) * 3
        bx = (pt2[0] - pt1[0]) * 3 - cx
        by = (pt2[1] - pt1[1]) * 3 - cy
        ax = pt3[0] - pt0[0] - cx - bx
        ay = pt3[1] - pt0[1] - cy - by
        t3 = t ** 3
        t2 = t * t
        x = ax * t3 + bx * t2 + cx * t + pt0[0]
        y = ay * t3 + by * t2 + cy * t + pt0[1]
        return x, y
