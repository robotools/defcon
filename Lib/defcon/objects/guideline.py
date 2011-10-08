import weakref
from defcon.objects.base import BaseDictObject
from defcon.tools.identifiers import makeRandomIdentifier


class Guideline(BaseDictObject):

    changeNotificationName = "Guideline.Changed"
    _identifiers = None

    # ----------
    # Properties
    # ----------

    def _get_x(self):
        return self.get("x")

    def _set_x(self, value):
        old = self.get("x")
        if value == old:
            return
        self["x"] = value
        self.postNotification("Guideline.XChanged", data=dict(oldX=old, newX=value))

    x = property(_get_x, _set_x, doc="The x coordinate. Setting this will post *Guideline.XChanged* and *Guideline.Changed* notifications.")

    def _get_y(self):
        return self.get("y")

    def _set_y(self, value):
        old = self.get("y")
        if value == old:
            return
        self["y"] = value
        self.postNotification("Guideline.YChanged", data=dict(oldY=old, newY=value))

    y = property(_get_y, _set_y, doc="The y coordinate. Setting this will post *Guideline.YChanged* and *Guideline.Changed* notifications.")

    def _get_angle(self):
        return self.get("angle")

    def _set_angle(self, value):
        old = self.get("angle")
        if value == old:
            return
        self["angle"] = value
        self.postNotification("Guideline.AngleChanged", data=dict(oldAngle=old, newAngle=value))

    angle = property(_get_angle, _set_angle, doc="The angle. Setting this will post *Guideline.AngleChanged* and *Guideline.Changed* notifications.")

    def _get_name(self):
        return self.get("name")

    def _set_name(self, value):
        old = self.get("name")
        if value == old:
            return
        self["name"] = value
        self.postNotification("Guideline.NameChanged", data=dict(oldName=old, newName=value))

    name = property(_get_name, _set_name, doc="The name. Setting this will post *Guideline.NameChanged* and *Guideline.Changed* notifications.")

    def _get_color(self):
        return self.get("color")

    def _set_color(self, color):
        if color is None:
            newColor = None
        else:
            newColor = Color(color)
        oldColor = self.get("color")
        if newColor == oldColor:
            return
        self["color"] = newColor
        self.postNotification("Guideline.ColorChanged", data=dict(old=oldColor, newColor=newColor))

    color = property(_get_color, _set_color, doc="The guideline's :class:`Color` object. When setting, the value can be a UFO color string, a sequence of (r, g, b, a) or a :class:`Color` object. Setting this posts *Guideline.ColorChanged* and *Guideline.Changed* notifications.")

    # -------
    # Methods
    # -------

    def _set_identifiers(self, value):
        self._identifiers = weakref.ref(value)

    def _get_identifiers(self):
        if self._identifiers is None:
            return set()
        return self._identifiers()

    identifiers = property(_get_identifiers, _set_identifiers, doc="Set of identifiers for the object that this guideline belongs to. This is primarily for internal use.")

    def _get_identifier(self):
        return self.get("identifier")

    def _set_identifier(self, value):
        oldIdentifier = self.identifier
        if value == oldIdentifier:
            return
        # don't allow a duplicate
        identifiers = self.identifiers
        assert value not in identifiers
        # free the old identifier
        if oldIdentifier in identifiers:
            identifiers.remove(oldIdentifier)
        # store
        self["identifier"] = value
        self.identifiers.add(value)
        # post notifications
        self.postNotification("Guideline.IdentifierChanged", data=dict(oldIdentifier=oldIdentifier, newIdentifier=value))

    identifier = property(_get_identifier, _set_identifier, doc="The identifier. Setting this will post *Guideline.IdentifierChanged* and *Guideline.Changed* notifications.")

    def generateIdentifier(self):
        """
        Create a new, unique identifier for and assign it to the guideline.
        This will post *Guideline.IdentifierChanged* and *Guideline.Changed* notifications.
        """
        identifier = makeRandomIdentifier(existing=self.identifiers)
        self.identifier = identifier


def _test():
    """
    >>> g = Guideline()
    >>> g.dirty
    False

    >>> g = Guideline()
    >>> g.x = 100
    >>> g.x
    100
    >>> g.dirty
    True
    >>> g.x = None
    >>> g.x
    >>> g.dirty
    True

    >>> g = Guideline()
    >>> g.y = 100
    >>> g.y
    100
    >>> g.dirty
    True
    >>> g.y = None
    >>> g.y
    >>> g.dirty
    True

    >>> g = Guideline()
    >>> g.angle = 100
    >>> g.angle
    100
    >>> g.dirty
    True
    >>> g.angle = None
    >>> g.angle
    >>> g.dirty
    True

    >>> g = Guideline()
    >>> g.name = "foo"
    >>> g.name
    'foo'
    >>> g.dirty
    True
    >>> g.name = None
    >>> g.name
    >>> g.dirty
    True

    >>> g = Guideline()
    >>> g.identifier
    >>> g.generateIdentifier()
    >>> g.identifier is None
    False
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
