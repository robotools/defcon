from robofab.pens.pointPen import AbstractPointPen

class GlyphObjectPointPen(AbstractPointPen):

    def __init__(self, glyph):
        self._glyph = glyph
        self._contour = None
        self._identifiers = glyph.identifiers

    def beginPath(self, identifier=None, **kwargs):
        if identifier is not None:
            assert identifier not in self.identifiers
        self._contour = self._glyph.contourClass(pointClass=self._glyph.pointClass)
        self._contour.identifier = identifier

    def endPath(self):
        if len(self._contour) == 1 and self._contour[0].name is not None:
            self._contour.identifier = None
            point = self._contour[0]
            anchor = self._glyph.anchorClass()
            anchor.x = point.x
            anchor.y = point.y
            anchor.name = point.name
            self._glyph.appendAnchor(anchor)
        else:
            self._contour.dirty = False
            # pull the identifier off, then reset it to
            # ensure that it makes it into the registry
            identifier = self._contour.identifier
            self._contour.identifier = None
            self._contour.identifiers = self._identifiers
            self._contour.identifier = identifier
            # store
            self._glyph.appendContour(self._contour)
        self._contour = None

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        if identifier is not None:
            assert identifier not in self.identifiers
        self._contour.addPoint(pt, segmentType, smooth, name, identifier=identifier, identifiers=self._identifiers)

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        if identifier is not None:
            assert identifier not in self.identifiers
        component = self._glyph.componentClass()
        component.baseGlyph = baseGlyphName
        component.transformation = transformation
        component.identifiers = self._glyph.identifiers
        component.identifier = identifier
        self._glyph.appendComponent(component)
