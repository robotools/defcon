from fontTools.pens.boundsPen import ControlBoundsPen, BoundsPen
from fontTools.misc.arrayTools import unionRect
from defcon.pens.clockwiseTestPointPen import ClockwiseTestPointPen

# -----
# Glyph
# -----

def glyphBoundsRepresentationFactory(glyph):
    bounds = None
    for group in (glyph, glyph.components):
        for obj in group:
            b = obj.bounds
            if b is not None:
                if bounds is None:
                    bounds = b
                else:
                    bounds = unionRect(bounds, b)
    return bounds

def glyphControlPointBoundsRepresentationFactory(glyph):
    bounds = None
    for group in (glyph, glyph.components):
        for obj in group:
            b = obj.controlPointBounds
            if b is not None:
                if bounds is None:
                    bounds = b
                else:
                    bounds = unionRect(bounds, b)
    return bounds

# -------
# Contour
# -------

# bounds

def contourBoundsRepresentationFactory(obj):
    pen = BoundsPen(None)
    obj.draw(pen)
    return pen.bounds

def contourControlPointBoundsRepresentationFactory(obj):
    pen = ControlBoundsPen(None)
    obj.draw(pen)
    return pen.bounds

# winding direction

def contourClockwiseRepresentationFactory(contour):
    pen = ClockwiseTestPointPen()
    contour.drawPoints(pen)
    return pen.getIsClockwise()
