from ufoLib.pointPen import AbstractPointPen

# adapted from robofab.objects.objectsBase.RContour._get_clockwise

class ClockwiseTestPointPen(AbstractPointPen):

    def __init__(self):
        self._points = []

    def beginPath(self):
        pass

    def endPath(self):
        pass

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        if segmentType:
            # overlapping points can give false results, so filter them out
            if self._points and self._points[-1] == pt:
                return
            self._points.append(pt)

    def getIsClockwise(self):
        import math
        points = self._points
        # overlapping moves can give false results, so filter them out
        if points[0] == points[-1]:
            del points[-1]
        angles = []
        pointCount = len(points)
        for index1 in range(pointCount):
            index2 = (index1 + 1) % pointCount
            x1, y1 = points[index1]
            x2, y2 = points[index2]
            angles.append(math.atan2(y2-y1, x2-x1))
        total = 0
        pi = math.pi
        pi2 = pi * 2
        for index1 in range(pointCount):
            index2 = (index1 + 1) % pointCount
            d = ((angles[index2] - angles[index1] + pi) % pi2) - pi
            total += d
        return total < 0