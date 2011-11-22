from defcon.objects.base import BaseDictObject


class Groups(BaseDictObject):

    """
    This object contains all of the groups in a font.

    **This object posts the following notifications:**

    ===================
    Name
    ===================
    Groups.Changed
    Groups.GroupSet
    Groups.GroupDeleted
    Groups.Cleared
    Groups.Updated
    ===================

    This object behaves like a dict. The keys are group names and the
    values are lists of glyph names::

        {
            "myGroup" : ["a", "b"],
            "myOtherGroup" : ["a.alt", "g.alt"],
        }

    The API for interacting with the data is the same as a standard dict.
    For example, to get a list of all group names::

        groupNames = groups.keys()

    To get all groups including the glyph lists::

        for groupName, glyphList in groups.items():

    To get the glyph list for a particular group name::

        glyphList = groups["myGroup"]

    To set the glyph list for a particular group name::

        groups["myGroup"] = ["x", "y", "z"]

    And so on.

    **Note:** You should not modify the group list and expect the object to
    know about it. For example, this could cause your changes to be lost::

        glyphList = groups["myGroups"]
        glyphList.append("n")

    To make sure the change is noticed, reset the list into the object::

        glyphList = groups["myGroups"]
        glyphList.append("n")
        groups["myGroups"] = glyphList

    This may change in the future.
    """

    changeNotificationName = "Groups.Changed"
    setItemNotificationName = "Groups.GroupSet"
    deleteItemNotificationName = "Groups.GroupDeleted"
    clearNotificationName = "Groups.Cleared"
    updateNotificationName = "Groups.Updated"
    representationFactories = {}

    def _get_font(self):
        return self.getParent()

    font = property(_get_font, doc="The :class:`Font` that this object belongs to.")


if __name__ == "__main__":
    import doctest
    doctest.testmod()
