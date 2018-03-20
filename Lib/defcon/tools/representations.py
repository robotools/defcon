from __future__ import absolute_import
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import ControlBoundsPen, BoundsPen
from fontTools.misc.arrayTools import unionRect
from fontPens.flattenPen import FlattenPen

# -----
# Glyph
# -----

def glyphBoundsRepresentationFactory(glyph):
    pen = BoundsPen(glyph.layer)
    glyph.draw(pen)
    return pen.bounds

def glyphControlPointBoundsRepresentationFactory(glyph):
    pen = ControlBoundsPen(glyph.layer)
    glyph.draw(pen)
    return pen.bounds

def glyphAreaRepresentationFactory(glyph):
    pen = AreaPen()
    glyph.draw(pen)
    return abs(pen.value)

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

# area

def contourAreaRepresentationFactory(contour):
    pen = AreaPen()
    contour.draw(pen)
    return pen.value

# flattened

def contourFlattenedRepresentationFactor(contour, approximateSegmentLength=5):
    from defcon.objects.glyph import Glyph
    contourClass = contour.__class__
    glyph = Glyph(contourClass=contourClass)
    outputPen = glyph.getPen()
    flattenPen = FlattenPen(outputPen, approximateSegmentLength=approximateSegmentLength)
    contour.draw(flattenPen)
    output = glyph[0]
    return output

# ---------
# Component
# ---------

# bounds

def componentBoundsRepresentationFactory(obj):
    pen = BoundsPen(obj.layer)
    obj.draw(pen)
    return pen.bounds

def componentPointBoundsRepresentationFactory(obj):
    pen = ControlBoundsPen(obj.layer)
    obj.draw(pen)
    return pen.bounds
