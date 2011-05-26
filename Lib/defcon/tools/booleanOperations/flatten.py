import math
from fontTools.pens.basePen import BasePen

# -------
# Objects
# -------

class Contour(list):

    # ----------
    # Attributes
    # ----------

    # finalized state

    def _get_final(self):
        for segment in self:
            if not segment.final:
                return False
        return True

    final = property(_get_final)

    # original segments

    def _get_original(self):
        all = []
        for segment in self:
            all.append((segment.type, segment.original))
        return all

    original = property(_get_original)

    # flattened segments

    def _get_flat(self):
        all = []
        for segment in self:
            all += segment.flat
        return all

    flat = property(_get_flat)

    # --------
    # Segments
    # --------

    def addSegment(self, type=None, original=None, flat=None):
        segment = Segment(type=type, original=original, flat=flat)
        self.append(segment)
        return segment

    def _setPrevPoints(self):
        for index, segment in enumerate(self):
            segment.prevPoint = self[index - 1].original[-1]
            segment.prevFlatPoint = self[index - 1].flat[-1]

    def tryToReplaceFlattenedWithOriginalSegment(self, segment):
        changed = self._tryToReplaceFlattenedWithOriginalSegment(segment)
        if not changed:
            changed = self._tryToReplaceFlattenedWithOriginalSegment(segment, reverse=True)

    def _tryToReplaceFlattenedWithOriginalSegment(self, segment, reverse=False):
        flattened = self.flat
        # quickly test if the edges of the segment are even in this contour
        prevPoint = segment.prevFlatPoint
        if prevPoint not in flattened:
            return False
        lastPoint = segment.flat[-1]
        if lastPoint not in flattened:
            return False
        # make a copy of the segments in this contour
        selfSegments = list(self)
        if reverse:
            selfSegments = list(reversed(selfSegments))
        # get all instances of the previous point
        prevPointIndexes = []
        for index, flatSegment in enumerate(selfSegments):
            if flatSegment.final or flatSegment.type != "flat":
                continue
            if prevPoint in flatSegment.flat:
                prevPointIndexes.append(index)
        # work through the points after the found points
        segmentLength = len(segment.flat)
        for prevPointIndex in prevPointIndexes:
            start = prevPointIndex + 1
            end = start + segmentLength
            selfSlice = selfSegments[start:end]
            wrapAround = None
            if len(selfSlice) < segmentLength:
                wrapAround = end - len(selfSegments)
                selfSlice += selfSegments[:wrapAround]
            haveMatch = True
            reason = None
            for index, selfSegment in enumerate(selfSlice):
                # segment has already been changed
                if selfSegment.final or selfSegment.type != "flat":
                    haveMatch = False
                    reason = selfSegment.final, selfSegment.type
                    break
                # points don't match
                selfPoint = selfSegment.flat[0]
                segmentPoint = segment.flat[index]
                if selfPoint != segmentPoint:
                    haveMatch = False
                    reason = 2
                    break
            # replace if a match has been found
            if haveMatch:
                print segment.type
                del self[start:end]
                self.insert(start, segment)
                if wrapAround:
                    del self[:wrapAround]
                # finish the segment
                segment.final = segment.original
                if reverse:
                    segment.final = [segment.prevPoint] + list(reversed(segment.final[1:]))
                segment.used = True
                return True
        # didn't do anything
        return False

    # ------
    # Output
    # ------

    def draw(self, pen):
        for segment in self:
            instruction = segment.type
            points = segment.final
            if instruction == "move":
                pen.moveTo(points[0])
            elif instruction == "line":
                pen.lineTo(points[0])
            elif instruction == "curve":
                pen.curveTo(*points)
            elif instruction == "qcurve":
                pen.qCurveTo(*points)
        pen.closePath()


class Segment(object):

    def __init__(self, type=None, original=None, flat=None):
        if flat is None:
            flat = []
        # segment type
        self.type = type
        # original segment points
        self.prevPoint = None
        self.original = original
        # flattened segment points
        self.prevFlatPoint = None
        self.flat = flat
        # final points
        self.final = None
        # used
        self.used = False

    def __repr__(self):
        return "<Segment: type=%s>" % self.type


# ----------------
# Curve Flattening
# ----------------

"""
The curve flattening code was forked and modified from RoboFab's FilterPen.
That code was written by Erik van Blokland.
"""

class FlattenPen(BasePen):

    def __init__(self, scale=1, approximateSegmentLength=5):
        BasePen.__init__(self, glyphSet=None)
        self._scale = scale
        self._approximateSegmentLength = approximateSegmentLength
        self._qCurveConversion = None
        # publicly accessible attributes
        self.contours = []

    def _prepPoint(self, pt):
        x, y = pt
        x = x * self._scale
        y = y * self._scale
        x = int(round(x))
        y = int(round(y))
        return (x, y)

    def _moveTo(self, pt):
        self.contours.append(Contour())
        self.contours[-1].addSegment(type="move", original=[pt], flat=[self._prepPoint(pt)])

    def _lineTo(self, pt):
        currentPoint = self.contours[-1][-1].original[-1]
        if pt == currentPoint:
            return
        self.contours[-1].addSegment(type="line", original=[pt], flat=[self._prepPoint(pt)])

    def _curveToOne(self, pt1, pt2, pt3):
        currentPoint = self.contours[-1][-1].original[-1]
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
            segment = self.contours[-1].addSegment(type="qcurve", original=self._qCurveConversion)
        else:
            segment = self.contours[-1].addSegment(type="curve", original=[pt1, pt2, pt3])
        flattened = segment.flat
        step = 1.0 / maxSteps
        factors = range(0, maxSteps + 1)
        for i in factors[1:]:
            pt = _getCubicPoint(i * step, currentPoint, pt1, pt2, pt3)
            flattened.append(self._prepPoint(pt))

    def _qCurveToOne(self, pt1, pt2):
        self._qCurveConversion = [pt1, pt2]
        BasePen._qCurveToOne(pt1, pt2)
        self._qCurveConversion = None

    def _closePath(self):
        firstPoint = self.contours[-1][0].original[-1]
        self.lineTo(firstPoint)
        self.contours[-1]._setPrevPoints()

    def _endPath(self):
        pass

    def addComponent(self, glyphName, transformation):
        pass


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
