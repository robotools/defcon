from fontTools.pens.basePen import BasePen
from flatten import FlattenPen
from pyClipper import PolyClipper # XXX this isn't the real thing


import pprint


class BooleanOperationManager(object):

    def __init__(self):
        self._curveToFlatCache = {}
        self._scale = 100000
        self._inverseScale = .00001

    def _scaleDownPoint(self, point):
        x, y = point
        x = x * self._inverseScale
        if int(x) == x:
            x = int(x)
        y = y * self._inverseScale
        if int(y) == y:
            y = int(y)
        return x, y

    def _getPreppedContours(self, contours):
        flattenPen = FlattenPen(scale=self._scale)
        for contour in contours:
            contour.draw(flattenPen)
        return flattenPen.contours

    def _getClipperContours(self, contourDicts):
        clipperContours = []
        for contourDict in contourDicts:
            contour = []
            for segment in contourDict:
                contour += segment["flat"]
            clipperContours.append(dict(coordinates=contour))
        return clipperContours

    def _drawResult(self, contours, outPen):
        for contour in contours:
            outPen.moveTo(self._scaleDownPoint(contour[0]))
            for point in contour[1:]:
                outPen.lineTo(self._scaleDownPoint(point))
            outPen.closePath()

    # -------
    # Flatten
    # -------

    def flatten(self, contours, outPen):
        pass

    # ------------------
    # Boolean Operations
    # ------------------

    def union(self, contours, outPen):
        contourDicts = self._getPreppedContours(contours)
        clipperContours = self._getClipperContours(contourDicts)
        clipper = PolyClipper.alloc().init()
        result = clipper.execute_operation_withOptions_(clipperContours, "union", dict(subjectFillType="noneZero", clipFillType="noneZero"))
        self._drawResult(result, outPen)
