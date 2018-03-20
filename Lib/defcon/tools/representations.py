from __future__ import absolute_import
from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import ControlBoundsPen, BoundsPen
from fontTools.misc.arrayTools import unionRect

# -----
# Glyph
# -----

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

def contourFlattenedRepresentationFactory(contour, approximateSegmentLength=5, segmentLines=False):
    from fontPens.flattenPen import FlattenPen
    from defcon.objects.glyph import Glyph
    contourClass = contour.__class__
    glyph = Glyph(contourClass=contourClass)
    outputPen = glyph.getPen()
    flattenPen = FlattenPen(outputPen, approximateSegmentLength=approximateSegmentLength, segmentLines=segmentLines)
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
