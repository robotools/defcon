from fontTools.pens.basePen import BasePen
from flatten import FlattenPen, Contour
from pyClipper import PolyClipper # XXX this isn't the real thing


"""
General Suggestions:
- Contours should only be sent here if they actually overlap.
  This can be checked easily using contour bounds.
- Only perform operations on closed contours.
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

    def _prepContours(self, contours):
        flattenPen = FlattenPen(scale=self._scale)
        for contour in contours:
            contour.draw(flattenPen)
        contours = flattenPen.contours
        for contour in contours:
            contour[0].type = "line"
        return contours

    def _getClipperContours(self, preppedContours):
        clipperContours = []
        for contour in preppedContours:
            clipperContours.append(dict(coordinates=contour.flat))
        return clipperContours

    # -------
    # Recurve
    # -------

    def _recurveResult(self, resultContours, originalContours):
        # replace untouched contours
        resultReplacements = []
        originalToRemove = []
        for resultIndex, resultContour in enumerate(resultContours):
            for originalIndex, originalContour in enumerate(originalContours):
                resultFlat = resultContour.flat
                originalFlat = originalContour.flat
                # test length
                if len(resultFlat) != len(originalFlat):
                    continue
                # try the contour as is
                if resultFlat == originalFlat:
                    originalToRemove.append(originalIndex)
                    resultReplacements.append((resultIndex, originalContour))
                    break
                # the contour could have been reversed
                elif resultFlat == [originalFlat[0]] + list(reversed(originalFlat[1:])):
                    originalToRemove.append(originalIndex)
                    resultReplacements.append((resultIndex, originalContour))
                    break
        for index in reversed(sorted(originalToRemove)):
            del originalContours[index]
        for index, contour in resultReplacements:
            # remove the clipper contour
            del resultContours[index]
            # insert the original contour
            resultContours.insert(index, contour)
            # set the original contour as final
            for segment in contour:
                segment.final = segment.original
        # search for untouched segments
        for resultContour in resultContours:
            if resultContour.final:
                continue
            for originalContour in originalContours:
                for segment in originalContour:
                    # skip used
                    if segment.used:
                        continue
                    # try to insert the segment
                    changed = resultContour.tryToReplaceFlattenedWithOriginalSegment(segment)
        # XXX convert the reamining flattened into segments
        # XXX this is where the curve fitting will need to happen
        for contour in resultContours:
            if contour.final:
                continue
            for index, segment in enumerate(contour):
                if segment.final or segment.type != "flat":
                    print segment.type, segment.final
                    continue
                if index == 0:
                    segment.type = "move"
                else:
                    segment.type = "line"
                segment.final = [self._scaleDownPoint(point) for point in segment.flat]
        # done
        return resultContours

    # ------------------
    # Boolean Operations
    # ------------------

    def _performOperation(self, operation, contours, outPen):
        # prep the contours
        originalContours = self._prepContours(contours)
        # XXX temporary
        clipperContours = []
        for contour in originalContours:
            clipperContours.append(dict(coordinates=contour.flat))
        clipper = PolyClipper.alloc().init()
        result = clipper.execute_operation_withOptions_(clipperContours, operation, dict(subjectFillType="noneZero", clipFillType="noneZero"))
        # /XXX
        # convert the results into contour objects
        resultContours = []
        for pointList in result:
            contour = Contour()
            for point in pointList:
                point = tuple(point)
                contour.addSegment(type="flat", flat=[point])
            # add a line from the end to the beginning
            # clipper filters these out, but we need them
            if contour[-1].flat != contour[0].flat:
                segment = contour.addSegment(type="flat")
                segment.flat = list(contour[0].flat)
            resultContours.append(contour)
        # recurve and curvefit
        final = self._recurveResult(resultContours, originalContours)
        # output the results
        for contour in final:
            contour.draw(outPen)

    def union(self, contours, outPen):
        self._performOperation("union", contours, outPen)
