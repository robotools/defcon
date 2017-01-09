"""
PointPen for reversing the winding direction of contours.
"""

from ufoLib.pointPen import AbstractPointPen


class ReverseContourPointPen(AbstractPointPen):
    """
    This is a PointPen that passes outline data to another PointPen, but
    reversing the winding direction of all contours. Components are simply
    passed through unchanged.

    Closed contours are reversed in such a way that the first point remains
    the first point.
    """

    def __init__(self, outputPointPen):
        self.pen = outputPointPen
        self.currentContour = None  # a place to store the points for the current sub path

    def _flushContour(self):
        pen = self.pen
        contour = self.currentContour
        if not contour:
            pen.beginPath(identifier=self.currentContourIdentifier)
            pen.endPath()
            return

        closed = contour[0][1] != "move"
        if not closed:
            lastSegmentType = "move"
        else:
            # Remove the first point and insert it at the end. When
            # the list of points gets reversed, this point will then
            # again be at the start. In other words, the following
            # will hold:
            #   for N in range(len(originalContour)):
            #       originalContour[N] == reversedContour[-N]
            contour.append(contour.pop(0))
            # Find the first on-curve point.
            firstOnCurve = None
            for i in range(len(contour)):
                if contour[i][1] is not None:
                    firstOnCurve = i
                    break
            if firstOnCurve is None:
                # There are no on-curve points, be basically have to
                # do nothing but contour.reverse().
                lastSegmentType = None
            else:
                lastSegmentType = contour[firstOnCurve][1]

        contour.reverse()
        if not closed:
            # Open paths must start with a move, so we simply dump
            # all off-curve points leading up to the first on-curve.
            while contour[0][1] is None:
                contour.pop(0)
        pen.beginPath(identifier=self.currentContourIdentifier)
        for pt, nextSegmentType, smooth, name, kwargs in contour:
            if nextSegmentType is not None:
                segmentType = lastSegmentType
                lastSegmentType = nextSegmentType
            else:
                segmentType = None
            pen.addPoint(pt, segmentType=segmentType, smooth=smooth, name=name, **kwargs)
        pen.endPath()

    def beginPath(self, identifier=None, **kwargs):
        assert self.currentContour is None
        self.currentContour = []
        self.currentContourIdentifier = identifier
        self.onCurve = []

    def endPath(self):
        assert self.currentContour is not None
        self._flushContour()
        self.currentContour = None

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        self.currentContour.append((pt, segmentType, smooth, name, kwargs))

    def addComponent(self, glyphName, transform, identifier=None, **kwargs):
        assert self.currentContour is None
        self.pen.addComponent(glyphName, transform, identifier=identifier, **kwargs)
