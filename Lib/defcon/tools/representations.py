from __future__ import absolute_import
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import ControlBoundsPen, BoundsPen
from fontTools.misc.arrayTools import unionRect

# -----
# Glyph
# -----

def glyphBoundsRepresentationFactory(glyph):
    pen = BoundsPen(glyph.getParent())
    glyph.draw(pen)
    return pen.bounds

def glyphControlPointBoundsRepresentationFactory(glyph):
    pen = ControlBoundsPen(glyph.getParent())
    glyph.draw(pen)
    return pen.bounds

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
    pen = AreaPen()
    pen.endPath = pen.closePath
    contour.draw(pen)
    return pen.value < 0

# ---------
# Component
# ---------

# bounds

def componentBoundsRepresentationFactory(obj):
    pen = BoundsPen(obj.font)
    obj.draw(pen)
    return pen.bounds

def componentPointBoundsRepresentationFactory(obj):
    pen = ControlBoundsPen(obj.font)
    obj.draw(pen)
    return pen.bounds
