import math
from fontTools.pens.basePen import BasePen
from robofab.pens.reverseContourPointPen import ReverseContourPointPen
from robofab.pens.adapterPens import PointToSegmentPen

"""
To Do:
- the stuff listed below
- curve fit
- probably need to find line segments that were shortened
  by the operation so that the curve fit doesn't try to turn
  them into curves
- need to know what kind of curves should be used for
  curve fit--curve or qcurve
- false curves and duplicate points need to be filtered early on

notes:
- the flattened segments *must* be cyclical.
  if they aren't, matching is almost impossible.


optimization ideas:
- the flattening of the output segment in the full contour
  matching is probably expensive.
- there should be a way to flag an input contour as
  entirely used so that it isn't tried and tried and
  tried for segment matches.
- do a faster test when matching segments: when a end
  match is found, jump back input length and grab the
  output segment. test for match with the input.
- cache input contour objects. matching these to incoming
  will be a little difficult because of point names and
  identifiers. alternatively, deal with those after the fact.
- some tests on input before conversion to input objects
  could yield significant speedups. would need to check
  each contour for self intersection and each
  non-self-intersectingcontour for collision with other
  contours. and contours that don't have a hit could be
  skipped. this cound be done roughly with bounds.
  this should probably be done by extenal callers.

test cases:
- untouched contour: make clockwise and counter-clockwise tests
  of the same contour
"""

# factors for transferring coordinates to and from Clipper

clipperScale = 100000
inverseClipperScale = 1.0 / clipperScale

# -------------
# Input Objects
# -------------

# Input

class InputContour(object):

    def __init__(self, contour):
        # gather the point data
        pointPen = ContourPointDataPen()
        contour.drawPoints(pointPen)
        points = pointPen.getData()
        reversedPoints = _reversePoints(points)
        # gather segments
        segments = _convertPointsToSegments(points)
        reversedSegments = _convertPointsToSegments(reversedPoints)
        # get the direction
        self.clockwise = contour.clockwise
        # store the gathered data
        if self.clockwise:
            self.clockwiseSegments = segments
            self.counterClockwiseSegments = reversedSegments
        else:
            self.clockwiseSegments = reversedSegments
            self.counterClockwiseSegments = segments
        # flag indicating if the contour has been used
        self.used = False

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
            flat.extend(segment.flat)
        return flat

    clockwiseFlat = property(_get_clockwiseFlat)

    # the counter-clockwise direction in flat segments

    def _get_counterClockwiseFlat(self):
        flat = []
        segments = self.counterClockwiseSegments
        for segment in segments:
            flat.extend(segment.flat)
        return flat

    counterClockwiseFlat = property(_get_counterClockwiseFlat)


class InputSegment(object):

    __slots__ = ["points", "previousOnCurve", "flat", "used"]

    def __init__(self, points=None, previousOnCurve=None):
        if points is None:
            points = []
        self.points = points
        pointsToFlatten = []
        self.previousOnCurve = previousOnCurve
        if self.segmentType == "qcurve":
            XXX
            # this shoudl be easy.
            # copy the quad to cubic from fontTools.pens.basePen
        elif self.segmentType == "curve":
            pointsToFlatten = [previousOnCurve] + [point.coordinates for point in points]
        else:
            assert len(points) == 1
            self.flat = [point.coordinates for point in points]
        if pointsToFlatten:
            self.flat = _flattenSegment(pointsToFlatten)
        self.flat = _scalePoints(self.flat, scale=clipperScale)
        self.used = False

    def _get_segmentType(self):
        return self.points[-1].segmentType

    segmentType = property(_get_segmentType)


class InputPoint(object):

    __slots__ = ["coordinates", "segmentType", "smooth", "name", "kwargs"]

    def __init__(self, coordinates, segmentType=None, smooth=False, name=None, kwargs=None):
        self.coordinates = coordinates
        self.segmentType = segmentType
        self.smooth = smooth
        self.name = name
        self.kwargs = kwargs

    def copy(self):
        copy = self.__class__(
            coordinates=self.coordinates,
            segmentType=self.segmentType,
            smooth=self.smooth,
            name=self.name,
            kwargs=self.kwargs
        )
        return copy


# -------------
# Input Support
# -------------

class ContourPointDataPen:

    """
    Point pen for gathering raw contour data.
    An instance of this pen may only be used for one contour.
    """

    def __init__(self):
        self._points = None

    def getData(self):
        """
        Return a list of normalized InputPoint objects
        for the contour drawn with this pen.
        """
        # organize the points into segments
        # 1. make sure there is an on curve
        haveOnCurve = False
        for point in self._points:
            if point.segmentType is not None:
                haveOnCurve = True
                break
        # 2. move the off curves to front of the list
        if haveOnCurve:
            _prepPointsForSegments(self._points)
        # done
        return self._points

    def beginPath(self):
        assert self._points is None
        self._points = []

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        assert segmentType != "move"
        data = InputPoint(
            coordinates=pt,
            segmentType=segmentType,
            smooth=smooth,
            name=name,
            kwargs=kwargs
        )
        self._points.append(data)

    def addComponent(self, baseGlyphName, transformation):
        raise NotImplementedError

def _prepPointsForSegments(points):
    """
    Move any off curves at the end of teh contour
    to the beginning of the contour. This makes
    segmentation easier.
    """
    while 1:
        point = points[-1]
        if point.segmentType:
            break
        else:
            point = points.pop()
            points.insert(0, point)
            continue
        break

def _copyPoints(points):
    """
    Make a shallow copy of the points.
    """
    copied = [point.copy() for point in points]
    return copied

def _reversePoints(points):
    """
    Reverse the points. This differs from the
    reversal point pen in RoboFab in that it doesn't
    worry about maintaing the start point position.
    That has no benefit within the context of this module.
    """
    # copy the points
    points = _copyPoints(points)
    # find the first on curve type and recycle
    # it for the last on curve type
    firstOnCurve = None
    for index, point in enumerate(points):
        if point.segmentType is not None:
            firstOnCurve = index
            break
    lastSegmentType = points[firstOnCurve].segmentType
    # reverse the points
    points = reversed(points)
    # work through the reversed remaining points
    final = []
    for point in points:
        segmentType = point.segmentType
        if segmentType is not None:
            point.segmentType = lastSegmentType
            lastSegmentType = segmentType
        final.append(point)
    # move any offcurves at the end of the points
    # to the start of the points
    _prepPointsForSegments(final)
    # done
    return final

def _convertPointsToSegments(points):
    """
    Compile points into InputSegment objects.
    """
    # get the last on curve
    previousOnCurve = None
    for point in reversed(points):
        if point.segmentType is not None:
            previousOnCurve = point.coordinates
            break
    assert previousOnCurve is not None
    # gather the segments
    offCurves = []
    segments = []
    for point in points:
        # off curve, hold.
        if point.segmentType is None:
            offCurves.append(point)
        else:
            segment = InputSegment(
                points=offCurves + [point],
                previousOnCurve=previousOnCurve
            )
            segments.append(segment)
            offCurves = []
            previousOnCurve = point.coordinates
    assert not offCurves
    return segments


# --------------
# Output Objects
# --------------

class OutputContour(object):

    def __init__(self, pointList):
        if pointList[0] == pointList[-1]:
            del pointList[-1]
        self.clockwise = _getClockwise(pointList)
        self.segments = [
            OutputSegment(
                segmentType="flat",
                points=[point]
            ) for point in pointList
        ]

    def _scalePoint(self, point):
        x, y = point
        x = x * inverseClipperScale
        if int(x) == x:
            x = int(x)
        y = y * inverseClipperScale
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
                        points=[
                            OutputPoint(
                                coordinates=point.coordinates,
                                segmentType=point.segmentType,
                                smooth=point.name,
                                name=point.name,
                                kwargs=point.kwargs
                            )
                            for point in inputSegment.points
                        ],
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
                        points=[
                            OutputPoint(
                                coordinates=point.coordinates,
                                segmentType=point.segmentType,
                                smooth=point.name,
                                name=point.name,
                                kwargs=point.kwargs
                            )
                            for point in inputSegment.points
                        ],
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
            segment.points = [
                OutputPoint(
                    coordinates=self._scalePoint(point),
                    segmentType="line"
                )
                for point in segment.points
            ]

    # ----
    # Draw
    # ----

    def drawPoints(self, pointPen):
        pointPen.beginPath()
        for segment in self.segments:
            for point in segment.points:
                kwargs = {}
                if point.kwargs is not None:
                    kwargs = point.kwargs
                pointPen.addPoint(
                    point.coordinates,
                    segmentType=point.segmentType,
                    smooth=point.smooth,
                    name=point.name,
                    **kwargs
                )
        pointPen.endPath()


class OutputSegment(object):

    __slots__ = ["segmentType", "points", "final"]

    def __init__(self, segmentType=None, points=None, final=False):
        self.segmentType = segmentType
        if points is None:
            points = []
        self.points = points
        self.final = final


class OutputPoint(InputPoint): pass


# -------------
# Ouput Support
# -------------

def _getClockwise(points):
    """
    Very quickly get the direction for points.
    This only works for contours that *do not*
    self-intersect. It works by finding the area
    of the polygon. positive is counter-clockwise,
    negative is clockwise.
    """
    # quickly make segments
    segments = zip(points, points[1:] + [points[0]])
    # get the area
    area = sum([x0 * y1 - x1 * y0 for ((x0, y0), (x1, y1)) in segments])
    return area <= 0

# ----------------
# Curve Flattening
# ----------------

"""
The curve flattening code was forked and modified from RoboFab's FilterPen.
That code was written by Erik van Blokland.
"""

def _scalePoints(points, scale=1, convertToInteger=True):
    """
    Scale points and optionally convert them to integers.
    """
    if convertToInteger:
        points = [
            (int(round(x * scale)), int(round(y * scale)))
            for (x, y) in points
        ]
    else:
        points = [(x * scale, y * scale) for (x, y) in points]
    return points

def _intPoint(pt):
    return int(round(pt[0])), int(round(pt[1]))

def _flattenSegment(segment, approximateSegmentLength=5):
    """
    Flatten the curve segment int a list of points.
    The first and last points in the segment must be
    on curves. The returned list of points will not
    include the first on curve point.

    false curves (where the off curves are not any
    different from the on curves) must not be sent here.
    duplicate points must not be sent here.
    """
    onCurve1, offCurve1, offCurve2, onCurve2 = segment
    # no possible steps
    est = _estimateCubicCurveLength(onCurve1, offCurve1, offCurve2, onCurve2) / approximateSegmentLength
    maxSteps = int(round(est))
    if maxSteps < 1:
        return [onCurve2]
    # a usable curve
    flat = []
    step = 1.0 / maxSteps
    factors = range(0, maxSteps + 1)
    for i in factors[1:]:
        pt = _getCubicPoint(i * step, onCurve1, offCurve1, offCurve2, onCurve2)
        flat.append(pt)
    return flat

def _distance(pt1, pt2):
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
        length += _distance(pta, ptb)
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
