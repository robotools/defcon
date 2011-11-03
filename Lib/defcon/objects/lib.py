from defcon.objects.base import BaseDictObject


class Lib(BaseDictObject):

    """
    This object contains arbitrary data.

    **This object posts the following notifications:**

    ===============
    Name
    ===============
    Lib.Changed
    Lib.ItemSet
    Lib.ItemDeleted
    Lib.Cleared
    Lib.Updated
    ===============

    This object behaves like a dict. For example, to get a particular
    item from the lib::

        data = lib["com.typesupply.someApplication.blah"]

    To set the glyph list for a particular group name::

        lib["com.typesupply.someApplication.blah"] = 123

    And so on.

    **Note 1:** It is best to keep the data below the top level as shallow
    as possible. Changes below the top level will go unnoticed by the defcon
    change notification system. These changes will be saved the next time you
    save the font, however.

    **Note 2:** The keys used for storing data in the lib should follow the
    reverse domain naming convention detailed in the
    `UFO specification <http://unifiedfontobject.org/filestructure/lib.html>`_.
    """

    changeNotificationName = "Lib.Changed"
    setItemNotificationName = "Lib.ItemSet"
    deleteItemNotificationName = "Lib.ItemDeleted"
    clearNotificationName = "Lib.Cleared"
    updateNotificationName = "Lib.Updated"


if __name__ == "__main__":
    import doctest
    doctest.testmod()