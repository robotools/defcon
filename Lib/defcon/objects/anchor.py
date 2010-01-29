from defcon.objects.base import BaseObject

class Anchor(BaseObject):

    """
    This object represents an anchor point.

    **This object posts the following notifications:**

    ==============  ====
    Name            Note
    ==============  ====
    Anchor.Changed  Posted when the *dirty* attribute is set.
    ==============  ====
    """

    _notificationName = "Anchor.Changed"

    def __init__(self):
        super(Anchor, self).__init__()
        self._x = None
        self._y = None
        self._name = None

    def _get_x(self):
        return self._x

    def _set_x(self, value):
        self._x = value
        self.dirty = True

    x = property(_get_x, _set_x, doc="The x coordinate. Setting this will post an *Anchor.Changed* notification.")

    def _get_y(self):
        return self._y

    def _set_y(self, value):
        self._y = value
        self.dirty = True

    y = property(_get_y, _set_y, doc="The y coordinate. Setting this will post an *Anchor.Changed* notification.")

    def _get_name(self):
        return self._name

    def _set_name(self, value):
        self._name = value
        self.dirty = True

    name = property(_get_name, _set_name, doc="The name of the anchor. Setting this will post an *Anchor.Changed* notification.")

    def move(self, (x, y)):
        """
        Move the anchor by **(x, y)**.

        This will post an *Anchor.Changed* notification.
        """
        self._x += x
        self._y += y
        self.dirty = True

    def draw(self, pen):
        """
        Draw the anchor with **pen**.
        """
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """
        Draw the anchor with **pointPen**.
        """
        pointPen.beginPath()
        pointPen.addPoint((self.x, self.y), segmentType="move", smooth=False, name=self.name)
        pointPen.endPath()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
