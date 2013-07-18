from fontTools.pens.basePen import BasePen
from flatten import InputContour, OutputContour
from pyClipper import PolyClipper # XXX this isn't the real thing
#from clipper import Clipper, PolyType, ClipType, PolyFillType, Point


"""
General Suggestions:
- Contours should only be sent here if they actually overlap.
  This can be checked easily using contour bounds.
- Only perform operations on closed contours.
- contours must have an on curve point
- some kind of a log
"""


class BooleanOperationManager(object):

    def _performOperation(self, operation, subjectContours, clipContours, outPen):
        # prep the contours
        subjectInputContours = [InputContour(contour) for contour in subjectContours if contour and len(contour) > 1]
        clipInputContours = [InputContour(contour) for contour in clipContours if contour and len(contour) > 1]
        inputContours = subjectInputContours + clipInputContours
        # XXX temporary

        clipperContours = []
        for contour in subjectInputContours:
           clipperContours.append(dict(coordinates=contour.originalFlat, role="subject"))
        for contour in clipInputContours:
           clipperContours.append(dict(coordinates=contour.originalFlat, role="clip"))

        clipper = PolyClipper.alloc().init()
        resultContours = clipper.execute_operation_withOptions_(clipperContours, operation, dict(subjectFillType="noneZero", clipFillType="noneZero"))

        # clipper = Clipper()
        # for contour in subjectInputContours:
        #     clipper.AddPolygon([Point(x, y) for x, y in contour.originalFlat], PolyType.Subject)
        # for contour in clipInputContours:
        #     clipper.AddPolygon([Point(x, y) for x, y in contour.originalFlat], PolyType.Clip)
        # resultContours = []
        # result = clipper.Execute(getattr(ClipType, operation.capitalize()) , resultContours, PolyFillType.NonZero, PolyFillType.NonZero)

        # the temporary Clipper wrapper is very, very slow
        # at converting back to Python structures. do it here
        # so that the profiling of this can be isolated.
        convertedContours = []
        for contour in resultContours:
            contour = [tuple(point) for point in contour]
            convertedContours.append(contour)
        resultContours = convertedContours
        # /XXX
        # convert to output contours
        outputContours = [OutputContour(contour) for contour in resultContours]
        # re-curve entire contour
        for inputContour in inputContours:
            for outputContour in outputContours:
                if outputContour.final:
                    continue
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
            outputContour.reCurveSubSegments(inputContours)
        # output the results
        for outputContour in outputContours:
            outputContour.drawPoints(outPen)
        # XXX return?
        return outputContours

    def union(self, contours, outPen):
        # XXX return?
        return self._performOperation("union", contours, [], outPen)
    
    def difference(self, subjectContours, clipContours, outPen):
        return self._performOperation("difference", subjectContours, clipContours, outPen)
    
    def intersection(self, subjectContours, clipContours, outPen):
        return self._performOperation("intersection", subjectContours, clipContours, outPen)
    
    def xor(self, subjectContours, clipContours, outPen):
        return self._performOperation("xor", subjectContours, clipContours, outPen)

    def getIntersections(self, contours):
        from flatten import _scalePoints, inverseClipperScale
        # prep the contours
        inputContours = [InputContour(contour) for contour in contours if contour and len(contour) > 1]
        # XXX temporary
        inputFlatPoints = set()
        clipperContours = []
        for contour in inputContours:
            clipperContours.append(dict(coordinates=contour.originalFlat, role="subject"))
            inputFlatPoints.update(contour.originalFlat)
        
        clipper = PolyClipper.alloc().init()
        resultContours = clipper.execute_operation_withOptions_(clipperContours, "union", dict(subjectFillType="noneZero", clipFillType="noneZero"))
        # the temporary Clipper wrapper is very, very slow
        # at converting back to Python structures. do it here
        # so that the profiling of this can be isolated.
        resultFlatPoints = set()
        for contour in resultContours:
            resultFlatPoints.update([tuple(point) for point in contour])
        
        intersections = resultFlatPoints - inputFlatPoints
        return _scalePoints(intersections, inverseClipperScale)


    