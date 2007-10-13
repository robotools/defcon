from defcon.objects.base import BaseObject


class Component(BaseObject):

    _notificationName = "Component.Changed"

    def __init__(self):
        super(Component, self).__init__()
        self._dirty = False
        self._baseGlyph = None
        self._transformation = (1, 0, 0, 1, 0, 0)

    def _set_baseGlyph(self, value):
        oldValue = self._baseGlyph
        self._baseGlyph = value
        self.dirty = True
        dispatcher = self.dispatcher
        if dispatcher is not None:
            dispatcher.postNotification(notification="Component.BaseGlyphChanged", observable=self, data=(oldValue, value))

    def _get_baseGlyph(self):
        return self._baseGlyph

    baseGlyph = property(_get_baseGlyph, _set_baseGlyph)

    def _set_transformation(self, value):
        self._transformation = value
        self.dirty = True

    def _get_transformation(self):
        return self._transformation

    transformation = property(_get_transformation, _set_transformation)

    #------------
    # pen methods
    #------------

    def draw(self, pen):
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        pointPen.addComponent(self._baseGlyph, self._transformation)

    #--------
    # methods
    #--------


if __name__ == "__main__":
    import doctest
    doctest.testmod()
