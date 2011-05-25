from fontTools.pens.basePen import BasePen
from flatten import FlattenPen
from pyClipper import PolyClipper # XXX this isn't the real thing


"""
general suggestions:
- contours should only be sent here if they actually overlap.
  this can be checked easily using contour bounds.
- only closed contours should be sent here.
"""


class BooleanOperationManager(object):

    def __init__(self):
        self._scale = 100000
        self._inverseScale = .00001

    # ---------------
    # Prep for Clipper
    # ---------------

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

    def _getClipperContours(self, preppedContours):
        clipperContours = []
        for contour in preppedContours:
            clipperContours.append(dict(coordinates=contour.flattened))
        return clipperContours

    # -------
    # Recurve
    # -------

    def _recurveResult(self, result, originalContours):
        # convert the contours into a trackable set of dicts
        result = [dict(fixed=False, recurved=[], flattened=contour) for contour in result]
        # check to see if any contours were completely untouched
        originalToRemove = []
        for contour in result:
            p = [tuple(point) for point in contour["flattened"]]
            for index, originalContour in enumerate(originalContours):
                if contour["flattened"] == originalContour.flattened:
                    contour["recurved"] = originalContour.original
                    contour["fixed"] = True
                    originalToRemove.append(index)
                    break
        for index in reversed(originalToRemove):
            del originalContours[index]
        # XXX convert flattened into segments
        for contour in result:
            if contour["fixed"]:
                continue
            points = contour["flattened"]
            contour["recurved"] = [("move", [self._scaleDownPoint(points[0])])]
            for point in points[1:]:
                point = self._scaleDownPoint(point)
                contour["recurved"].append(("line", [point]))
            contour["fixed"] = True
        # convert the result into a set of pen instructions
        final = []
        for contour in result:
            final.append(contour["recurved"])
        return final

    # -----------------
    # Output the Result
    # -----------------

    def _drawResult(self, contours, outPen):
        for contour in contours:
            for segment in contour:
                instruction = segment[0]
                points = segment[1]
                if instruction == "move":
                    outPen.moveTo(points[0])
                elif instruction == "line":
                    outPen.lineTo(points[0])
                elif instruction == "curve":
                    outPen.curveTo(*points)
                elif instruction == "qcurve":
                    outPen.qCurveTo(*points)
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
        originalContours = self._getPreppedContours(contours)
        clipperContours = self._getClipperContours(originalContours)
        clipper = PolyClipper.alloc().init()
        result = clipper.execute_operation_withOptions_(clipperContours, "union", dict(subjectFillType="noneZero", clipFillType="noneZero"))
        result = self._recurveResult(result, originalContours)
        self._drawResult(result, outPen)
