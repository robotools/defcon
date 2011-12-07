from ufoLib.pointPen import AbstractPointPen

class GlyphObjectPointPen(AbstractPointPen):

    def __init__(self, glyph):
        self._glyph = glyph
        self._contour = None
        self.skipConflictingIdentifiers = False

    def beginPath(self, identifier=None, **kwargs):
        self._contour = self._glyph.instantiateContour()
        self._contour.disableNotifications()
        if identifier is not None:
            if self.skipConflictingIdentifiers and identifier in self._glyph.identifiers:
                pass
            else:
                self._contour.identifier = identifier

    def endPath(self):
        self._contour.dirty = False
        self._glyph.appendContour(self._contour)
        self._contour.enableNotifications()
        self._contour = None

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        if self.skipConflictingIdentifiers and identifier in self._glyph.identifiers:
            identifier = None
        self._contour.addPoint(pt, segmentType, smooth, name, identifier=identifier)

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        if self.skipConflictingIdentifiers and identifier in self._glyph.identifiers:
            identifier = None
        component = self._glyph.instantiateComponent()
        component.baseGlyph = baseGlyphName
        component.transformation = transformation
        component.identifier = identifier
        self._glyph.appendComponent(component)
