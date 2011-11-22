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
    representationFactories = {}

    # parents

    def _get_font(self):
        from defcon.objects.glyph import Glyph
        parent = self.getParent()
        if isinstance(parent, Glyph):
            return parent.font
        return parent

    font = property(_get_font, doc="The :class:`Font` that this object belongs to.")

    def _get_layerSet(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.layerSet

    layerSet = property(_get_layerSet, doc="The :class:`LayerSet` that this object belongs to (if it isn't a font lib).")

    def _get_layer(self):
        glyph = self.glyph
        if glyph is None:
            return None
        return glyph.layer

    layer = property(_get_layer, doc="The :class:`Layer` that this object belongs to (if it isn't a font lib).")

    def _get_glyph(self):
        from defcon.objects.font import Font
        parent = self.getParent()
        if isinstance(parent, Font):
            return None
        return parent

    glyph = property(_get_glyph, doc="The :class:`Glyph` that this object belongs to (if it isn't a font lib).")



if __name__ == "__main__":
    import doctest
    doctest.testmod()