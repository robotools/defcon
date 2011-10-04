from robofab.pens.pointPen import AbstractPointPen

class GlyphObjectPointPen(AbstractPointPen):
    
    def __init__(self, glyph, identifiers=None):
        self._glyph = glyph
        self._contour = None
        self.identifiers = identifiers

    def beginPath(self, identifier=None, **kwargs):
        assert identifier not in self.identifiers
        self._contour = self._glyph.contourClass(pointClass=self._glyph.pointClass)

    def endPath(self):
        if len(self._contour) == 1 and self._contour[0].name is not None:
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

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        assert identifier not in self.identifiers
        self._contour.addPoint(pt, segmentType, smooth, name)

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        assert identifier not in self.identifiers
        component = self._glyph.componentClass()
        component.baseGlyph = baseGlyphName
        component.transformation = transformation
        self._glyph.appendComponent(component)
