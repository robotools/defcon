from robofab.pens.pointPen import AbstractPointPen

class GlyphObjectPointPen(AbstractPointPen):
    
    def __init__(self, glyph):
        self._glyph = glyph
        self._contour = None

    def beginPath(self):
        self._contour = self._glyph.contourClass()

    def endPath(self):
        if len(self._contour) == 1:
            point = self._contour[0]
            anchor = self._glyph.anchorClass()
            anchor.x = point.x
            anchor.y = point.y
            anchor.name = point.name
            self._glyph.appendAnchor(anchor)
        else:
            self._contour.dirty = False
            self._glyph.appendContour(self._contour)
        self._contour = None

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, **kwargs):
        self._contour.addPoint(pt, segmentType, smooth, name)

    def addComponent(self, baseGlyphName, transformation):
        component = self._glyph.componentClass()
        component.baseGlyph = baseGlyphName
        component.transformation = transformation
        self._glyph.appendComponent(component)
