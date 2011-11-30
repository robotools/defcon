from robofab.pens.pointPen import AbstractPointPen

class GlyphObjectPointPen(AbstractPointPen):

    def __init__(self, glyph):
        self._glyph = glyph
        self._contour = None

    def beginPath(self, identifier=None, **kwargs):
        self._contour = self._glyph.instantiateContour()
        self._contour.disableNotifications()
        self._contour.identifier = identifier

    def endPath(self):
        self._contour.dirty = False
        self._glyph.appendContour(self._contour)
        self._contour.enableNotifications()
        self._contour = None

    def addPoint(self, pt, segmentType=None, smooth=False, name=None, identifier=None, **kwargs):
        self._contour.addPoint(pt, segmentType, smooth, name, identifier=identifier)

    def addComponent(self, baseGlyphName, transformation, identifier=None, **kwargs):
        component = self._glyph.componentClass()
        component.baseGlyph = baseGlyphName
        component.transformation = transformation
        component.identifier = identifier
        self._glyph.appendComponent(component)
