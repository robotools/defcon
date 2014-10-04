class Point(object):

    """
    This object represents a single point.
    """

    __slots__ = ["_x", "_y", "_segmentType", "_smooth", "_name"]

    def __init__(self, xxx_todo_changeme, segmentType=None, smooth=False, name=None):
        (x, y) = xxx_todo_changeme
        self._x = x
        self._y = y
        self._segmentType = segmentType
        self._smooth = smooth
        self._name = name

    def __repr__(self):
        return "<%s position: (%s, %s) type: %s smooth: %s name: %s>" % (self.__class__.__name__, self.x, self.y, str(self.segmentType), str(self.smooth), str(self.name))

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

    def move(self, xxx_todo_changeme1):
        """
        Move the component by **(x, y)**.
        """
        (x, y) = xxx_todo_changeme1
        self.x += x
        self.y += y

    # ----
    # Undo
    # ----

    def getDataToSerializeForUndo(self):
        data = dict(
            x=self.x,
            y=self.y,
            segmentType=self.segmentType,
            smooth=self.smooth,
            name=self.name
        )
        return data

    def loadDeserializedDataFromUndo(self, data):
        self.x = data["x"]
        self.y = data["y"]
        self.segmentType = data["segmentType"]
        self.smooth = data["smooth"]
        self.name = data["name"]


if __name__ == "__main__":
    import doctest
    doctest.testmod()