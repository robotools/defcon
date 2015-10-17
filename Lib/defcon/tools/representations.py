from __future__ import absolute_import
from fontTools.pens.boundsPen import ControlBoundsPen, BoundsPen
from fontTools.misc.arrayTools import unionRect
from defcon.pens.clockwiseTestPointPen import ClockwiseTestPointPen

# -----
# Glyph
# -----

def glyphBoundsRepresentationFactory(glyph):
    # base glyph
    pen = BoundsPen(glyph.getParent())
    glyph.draw(pen)
    bounds = pen.bounds
    # components
    for component in glyph.components:
        b = component.bounds
        if b is not None:
            if bounds is None:
                bounds = b
            else:
                bounds = unionRect(bounds, b)
    return bounds

def glyphControlPointBoundsRepresentationFactory(glyph):
    # base glyph
    pen = ControlBoundsPen(glyph.getParent())
    glyph.draw(pen)
    bounds = pen.bounds
    # components
    for component in glyph.components:
        b = component.controlPointBounds
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
