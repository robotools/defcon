from robofab.pens.pointPen import AbstractPointPen

class GlyphObjectPointPen(AbstractPointPen):

    def __init__(self, glyph):
        self._glyph = glyph
        self._contour = None

    def beginPath(self, identifier=None, **kwargs):
        self._contour = self._glyph.contourClass(pointClass=self._glyph.pointClass)
        self._contour.identifier = identifier

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
        self._contour.addPoint(pt, segmentType, smooth, name, identifier=identifier)

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        component = self._glyph.componentClass()
        component.baseGlyph = baseGlyphName
        component.transformation = transformation
        component.identifier = identifier
        self._glyph.appendComponent(component)
