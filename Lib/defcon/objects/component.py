from fontTools.misc.transform import Transform
from defcon.objects.base import BaseObject

_defaultTransformation = (1, 0, 0, 1, 0, 0)

class Component(BaseObject):

    """
    This object represents a reference to another glyph.

    **This object posts the following notifications:**

    ==========================  ====
    Name                        Note
    ==========================  ====
    Component.Changed           Posted when the *dirty* attribute is set.
    Component.BaseGlyphChanged  Posted when the *baseGlyph* attribute is set.
    ==========================  ====
    """

    changeNotificationName = "Component.Changed"

    def __init__(self):
        super(Component, self).__init__()
        self._dirty = False
        self._baseGlyph = None
        self._transformation = tuple(_defaultTransformation)

    # ----------
    # Attributes
    # ----------

    def _getBounds(self, boundsAttr):
        glyph = self.getParent()
        if glyph is None:
            return None
        font = glyph.getParent()
        if font is None:
            return None
        if self.baseGlyph not in font:
            return None
        glyph = font[self.baseGlyph]
        bounds = getattr(glyph, boundsAttr)
        if bounds is None:
            return None
        if self.transformation == _defaultTransformation:
            return bounds
        xMin, yMin, xMax, yMax = bounds
        t = Transform(*self.transformation)
        points = [(xMin, yMin), (xMax, yMax)]
        (xMin, yMin), (xMax, yMax) = t.transformPoints(points)
        return xMin, yMin, xMax, yMax

    def _get_bounds(self):
        return self._getBounds("bounds")

    bounds = property(_get_bounds, doc="The bounds of the components's outline expressed as a tuple of form (xMin, yMin, xMax, yMax).")

    def _get_controlPointBounds(self):
        return self._getBounds("controlPointBounds")

    controlPointBounds = property(_get_controlPointBounds, doc="The control bounds of all points in the components. This only measures the point positions, it does not measure curves. So, curves without points at the extrema will not be properly measured.")

    def _set_baseGlyph(self, value):
        oldValue = self._baseGlyph
        self._baseGlyph = value
        self.dirty = True
        dispatcher = self.dispatcher
        if dispatcher is not None:
            dispatcher.postNotification(notification="Component.BaseGlyphChanged", observable=self, data=(oldValue, value))

    def _get_baseGlyph(self):
        return self._baseGlyph

    baseGlyph = property(_get_baseGlyph, _set_baseGlyph, doc="The glyph that the components references. Setting this will post *Component.BaseGlyphChanged* and *Component.Changed* notifications.")

    def _set_transformation(self, value):
        self._transformation = value
        self.dirty = True

    def _get_transformation(self):
        return self._transformation

    transformation = property(_get_transformation, _set_transformation, doc="The transformation matrix for the component. Setting this will posts a *Component.Changed* notification.")

    # -----------
    # Pen Methods
    # -----------

    def draw(self, pen):
        """
        Draw the component with **pen**.
        """
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """
        Draw the component with **pointPen**.
        """
        pointPen.addComponent(self._baseGlyph, self._transformation)

    # -------
    # Methods
    # -------

    def move(self, (x, y)):
        """
        Move the component by **(x, y)**.

        This posts a *Component.Changed* notification.
        """
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = self._transformation
        xOffset += x
        yOffset += y
        self.transformation = (xScale, xyScale, yxScale, yScale, xOffset, yOffset)

    def pointInside(self, (x, y), evenOdd=False):
        """
        Returns a boolean indicating if **(x, y)** is in the
        "black" area of the component.
        """
        from fontTools.pens.pointInsidePen import PointInsidePen
        glyph = self.getParent()
        if glyph is None:
            return False
        font = self.getParent()
        if font is None:
            return False
        pen = PointInsidePen(glyphSet=font, testPoint=(x, y), evenOdd=evenOdd)
        self.draw(pen)
        return pen.getResult()

    # ----
    # Undo
    # ----

    def getDataToSerializeForUndo(self):
        data = dict(
            baseGlyph=self.baseGlyph,
            transformation=self.transformation
        )
        return data

    def loadDeserializedDataFromUndo(self, data):
        self.baseGlyph = data["baseGlyph"]
        self.transformation = data["transformation"]


if __name__ == "__main__":
    import doctest
    doctest.testmod()
