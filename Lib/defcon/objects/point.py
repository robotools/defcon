class Point(object):

    """
    This object represents a single point.
    """

    __slots__ = ["_x", "_y", "_segmentType", "_smooth", "_name"]

    def __init__(self, (x, y), segmentType=None, smooth=False, name=None):
        self._x = x
        self._y = y
        self._segmentType = segmentType
        self._smooth = smooth
        self._name = name

    def __repr__(self):
        return "<Point position: (%s, %s) type: %s smooth: %s name: %s>" % (self.x, self.y, str(self.segmentType), str(self.smooth), str(self.name))

    def _get_segmentType(self):
        return self._segmentType

    def _set_segmentType(self, value):
        self._segmentType = value

    segmentType = property(_get_segmentType, _set_segmentType, doc="The segment type. The positibilies are *move*, *line*, *curve*, *qcurve* and *None* (indicating that this is an off-curve point).")

    def _get_x(self):
        return self._x

    def _set_x(self, value):
        self._x = value

    x = property(_get_x, _set_x, doc="The x coordinate.")

    def _get_y(self):
        return self._y

    def _set_y(self, value):
        self._y = value

    y = property(_get_y, _set_y, doc="The y coordinate.")

    def _get_smooth(self):
        return self._smooth

    def _set_smooth(self, value):
        self._smooth = value

    smooth = property(_get_smooth, _set_smooth, doc="A boolean indicating the smooth state of the point.")

    def _get_name(self):
        return self._name

    def _set_name(self, value):
        self._name = value

    name = property(_get_name, _set_name, doc="An arbitrary name for the point.")

    def move(self, (x, y)):
        """
        Move the component by **(x, y)**.
        """
        self._x += x
        self._y += y


if __name__ == "__main__":
    import doctest
    doctest.testmod()