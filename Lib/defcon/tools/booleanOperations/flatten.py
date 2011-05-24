"""
The curve to flattened segments code was forked and modified from
RoboFab's filterPen. That code was written by Erik van Blokland.

The major modifications:
- an out pen is not used
- doubles are always filtered
- there is no support for line splitting
- components are ignored
- a cache of flat -> curve is maintained
- floats are not supported by the Clipper library,
  so there is an option for scaling the contour
  during flattening


"""

import math
from fontTools.pens.basePen import BasePen

# ----------------
# Curve Flattening
# ----------------

def _segment(type=None, original=None, flat=None):
    if flat is None:
        flat = []
    d = dict(
        type=type,
        original=original,
        flat=flat
    )
    return d


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
        segment = _segment(type="move", original=[pt], flat=[self._prepPoint(pt)])
        self.contours[-1].append(segment)

    def _lineTo(self, pt):
        currentPoint = self.contours[-1][-1]["original"][-1]
        if pt == currentPoint:
            return
        segment = _segment(type="line", original=[pt], flat=[self._prepPoint(pt)])
        self.contours[-1].append(segment)

    def _curveToOne(self, pt1, pt2, pt3):
        currentPoint = self.contours[-1][-1]["original"][-1]
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
            segment = _segment(type="qcurve", original=self._qCurveConversion)
        else:
            segment = _segment(type="curve", original=[pt1, pt2, pt3])
        flattened = segment["flat"]
        step = 1.0 / maxSteps
        factors = range(0, maxSteps + 1)
        for i in factors[1:]:
            pt = _getCubicPoint(i * step, currentPoint, pt1, pt2, pt3)
            flattened.append(self._prepPoint(pt))
        self.contours[-1].append(segment)

    def _qCurveToOne(self, pt1, pt2):
        self._qCurveConversion = [pt1, pt2]
        BasePen._qCurveToOne(pt1, pt2)
        self._qCurveConversion = None

    def _closePath(self):
        self.lineTo(self.contours[-1][0]["original"][-1])
        self.endPath()

    def _endPath(self):
        if self.contours[-1][0]["flat"][0] == self.contours[-1][-1]["flat"][-1]:
            del self.contours[-1][-1]["flat"][-1]

    def addComponent(self, glyphName, transformation):
        pass


class Contour(list):

    def _get_original(self):
        all = []
        for segment in self:
            all.append((segment["type"], segment["original"]))
        return all

    original = property(_get_original)

    def _get_flattened(self):
        all = []
        for segment in self:
            all += segment["flat"]
        return all

    flattened = property(_get_flattened)


# -----------------
# Support Functions
# -----------------

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
