from fontTools.pens.basePen import BasePen
from flatten import InputContour, OutputContour
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
        self._inverseScale = 1.0 / self._scale

    # ------------------
    # Boolean Operations
    # ------------------

    def _performOperation(self, operation, contours, outPen):
        # prep the contours
        inputContours = [InputContour(contour, scale=self._scale) for contour in contours]
        # XXX temporary
        clipperContours = []
        for contour in inputContours:
            clipperContours.append(dict(coordinates=contour.originalFlat))
        clipper = PolyClipper.alloc().init()
        resultContours = clipper.execute_operation_withOptions_(clipperContours, operation, dict(subjectFillType="noneZero", clipFillType="noneZero"))
        # /XXX
        # convert to output contours
        outputContours = [OutputContour(contour, scale=self._inverseScale) for contour in resultContours]
        # re-curve entire contour
        for inputContour in inputContours:
            for outputContour in outputContours:
                if outputContour.final:
                    break
                if outputContour.reCurveFromEntireInputContour(inputContour):
                    # the input is expired if a match was made,
                    # so stop passing it to the outputs
                    break
        # re-curve segments
        for inputContour in inputContours:
            # skip contours that were comppletely used in the previous step
            if inputContour.used:
                continue
            # XXX this could be expensive if an input becomes completely used
            # it doesn't stop from being passed to the output
            for outputContour in outputContours:
                outputContour.reCurveFromInputContourSegments(inputContour)
        # curve fit
        for outputContour in outputContours:
            outputContour.curveFit()
        # outout the results
        for outputContour in outputContours:
            outputContour.draw(outPen)

    def union(self, contours, outPen):
        self._performOperation("union", contours, outPen)
