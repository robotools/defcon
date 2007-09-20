from defcon.objects.base import BaseObject

class Anchor(BaseObject):

    def __init__(self, dispatcher=None):
        super(Anchor, self).__init__(dispatcher)
        self._x = None
        self._y = None
        self._name = None

    def _get_x(self):
        return self._x

    def _set_x(self, value):
        self._x = value

    x = property(_get_x, _set_x)

    def _get_y(self):
        return self._y

    def _set_y(self, value):
        self._y = value

    y = property(_get_y, _set_y)

    def _get_name(self):
        return self._name

    def _set_name(self, value):
        self._name = value

    name = property(_get_name, _set_name)

    def move(self, (x, y)):
        self._x += x
        self._y += y
        self.dirty = True

    def draw(self, pen):
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        pass

if __name__ == "__main__":
    import doctest
    doctest.testmod()
