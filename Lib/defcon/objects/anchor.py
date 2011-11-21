from defcon.objects.base import BaseDictObject
from defcon.objects.color import Color
from defcon.tools.identifiers import makeRandomIdentifier


class Anchor(BaseDictObject):

    """
    This object represents an anchor point.

    **This object posts the following notifications:**

    ========================
    Name
    ========================
    Anchor.Changed
    Anchor.XChanged
    Anchor.YChanged
    Anchor.NameChanged
    Anchor.ColorChanged
    Anchor.IdentifierChanged
    ========================

    During initialization an anchor dictionary can be passed. If so,
    the new object will be populated with the data from the dictionary.
    """

    changeNotificationName = "Anchor.Changed"
    representationFactories = {}

    def __init__(self, anchorDict=None):
        super(Anchor, self).__init__()
        self._dirty = False
        if anchorDict is not None:
            self.x = anchorDict.get("x")
            self.y = anchorDict.get("y")
            self.name = anchorDict.get("name")
            self.color = anchorDict.get("color")
            self.identifier = anchorDict.get("identifier")

    def _get_x(self):
        return self.get("x")

    def _set_x(self, value):
        old = self.get("x")
        if value == old:
            return
        self["x"] = value
        self.postNotification("Anchor.XChanged", data=dict(oldValue=old, newValue=value))

    x = property(_get_x, _set_x, doc="The x coordinate. Setting this will post *Anchor.XChanged* and *Anchor.Changed* notifications.")

    def _get_y(self):
        return self.get("y")

    def _set_y(self, value):
        old = self.get("y")
        if value == old:
            return
        self["y"] = value
        self.postNotification("Anchor.YChanged", data=dict(oldValue=old, newValue=value))

    y = property(_get_y, _set_y, doc="The y coordinate. Setting this will post *Anchor.YChanged* and *Anchor.Changed* notifications.")

    def _get_name(self):
        return self.get("name")

    def _set_name(self, value):
        old = self.get("name")
        if value == old:
            return
        self["name"] = value
        self.postNotification("Anchor.NameChanged", data=dict(oldValue=old, newValue=value))

    name = property(_get_name, _set_name, doc="The name. Setting this will post *Anchor.NameChanged* and *Anchor.Changed* notifications.")

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
        self.postNotification("Anchor.ColorChanged", data=dict(oldValue=oldColor, newValue=newColor))

    color = property(_get_color, _set_color, doc="The anchors's :class:`Color` object. When setting, the value can be a UFO color string, a sequence of (r, g, b, a) or a :class:`Color` object. Setting this posts *Anchor.ColorChanged* and *Anchor.Changed* notifications.")

    # -------
    # Methods
    # -------

    def move(self, (x, y)):
        """
        Move the anchor by **(x, y)**.

        This will post *Anchor.XChange*, *Anchor.YChanged* and *Anchor.Changed* notifications if anything changed.
        """
        self.x += x
        self.y += y

    def _get_identifiers(self):
        identifiers = None
        parent = self.getParent()
        if parent is not None:
            identifiers = parent.identifiers
        if identifiers is None:
            identifiers = set()
        return identifiers

    identifiers = property(_get_identifiers, doc="Set of identifiers for the glyph that this anchor belongs to. This is primarily for internal use.")

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
        if value is not None:
            identifiers.add(value)
        # post notifications
        self.postNotification("Anchor.IdentifierChanged", data=dict(oldValue=oldIdentifier, newValue=value))

    identifier = property(_get_identifier, _set_identifier, doc="The identifier. Setting this will post *Anchor.IdentifierChanged* and *Anchor.Changed* notifications.")

    def generateIdentifier(self):
        """
        Create a new, unique identifier for and assign it to the guideline.
        This will post *Anchor.IdentifierChanged* and *Anchor.Changed* notifications.
        """
        identifier = makeRandomIdentifier(existing=self.identifiers)
        self.identifier = identifier


def _test():
    """
    >>> a = Anchor()
    >>> a.dirty
    False

    >>> a = Anchor()
    >>> a.x = 100
    >>> a.x
    100
    >>> a.dirty
    True

    >>> a = Anchor()
    >>> a.y = 100
    >>> a.y
    100
    >>> a.dirty
    True

    >>> a = Anchor()
    >>> a.name = "foo"
    >>> a.name
    'foo'
    >>> a.dirty
    True
    >>> a.name = None
    >>> a.name
    >>> a.dirty
    True

    >>> a = Anchor()
    >>> a.color = "1,1,1,1"
    >>> a.color
    '1,1,1,1'
    >>> a.dirty
    True

    >>> a = Anchor()
    >>> a.identifier
    >>> a.generateIdentifier()
    >>> a.identifier is None
    False

    >>> a = Anchor(dict(x=1, y=2, name="3", identifier="4", color="1,1,1,1"))
    >>> a.x, a.y, a.name, a.identifier, a.color
    (1, 2, '3', '4', '1,1,1,1')
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
