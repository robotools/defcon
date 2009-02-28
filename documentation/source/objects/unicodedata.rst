.. highlight:: python

============
Unicode Data
============

.. seealso::

   :ref:`Notifications`:
      The UnicodeData object uses notifications to notify observers of changes.

Types of Values
---------------

This object works with three types of Unicode values: *real*, *pseudo* and *forced*. A *real* Unicode value is the value assigned in the glyph object. A *pseudo*-Unicode value is an educated guess about what the Unicode value for the glyph could be. This guess is made by splitting the suffix, if one exists, off of the glyph name and then looking up the resulting base in the UnicodeData object. If something is found, the value is the pseudo-Unicode value. A *forced*-Unicode value is a Private Use Area value that is temporaryily mapped to a glyph in the font. These values are stored in the font object only as long as the font is active. They will not be saved into the font. **Note:** Forced-Unicode values are very experimental. They should not be relied upon.

Tasks
-----

Value From Glyph Name
"""""""""""""""""""""

* :attr:`~defcon.UnicodeData.unicodeForGlyphName`
* :attr:`~defcon.UnicodeData.pseudoUnicodeForGlyphName`
* :attr:`~defcon.UnicodeData.forcedUnicodeForGlyphName`

Glyph Name from Value
""""""""""""""""""""""

* :attr:`~defcon.UnicodeData.glyphNameForForcedUnicode`
* :attr:`~defcon.UnicodeData.glyphNameForUnicode`

Glyph Descriptions
""""""""""""""""""

* :attr:`~defcon.UnicodeData.blockForGlyphName`
* :attr:`~defcon.UnicodeData.categoryForGlyphName`
* :attr:`~defcon.UnicodeData.scriptForGlyphName`

Open and Closed Relatives
"""""""""""""""""""""""""

* :attr:`~defcon.UnicodeData.closeRelativeForGlyphName`
* :attr:`~defcon.UnicodeData.openRelativeForGlyphName`

Decomposition
"""""""""""""

* :attr:`~defcon.UnicodeData.decompositionBaseForGlyphName`

Sorting Glyphs
""""""""""""""

* :meth:`~defcon.UnicodeData.sortGlyphNames`

Notifications
"""""""""""""

* :attr:`~defcon.UnicodeData.dispatcher`
* :meth:`~defcon.UnicodeData.addObserver`
* :meth:`~defcon.UnicodeData.removeObserver`
* :meth:`~defcon.UnicodeData.hasObserver`

Parent
""""""

* :meth:`~defcon.UnicodeData.getParent`
* :meth:`~defcon.UnicodeData.setParent`

UnicodeData
^^^^^^^^^^^

.. module:: defcon
.. autoclass:: UnicodeData
   :inherited-members:
   :members:

