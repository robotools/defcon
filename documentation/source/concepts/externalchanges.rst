.. highlight:: python

.. _External_Changes:

================
External Changes
================

It may be advantagious for your application to notice changes to a UFO that were made outside of your application. the :class:`~defcon.Font` object can help you with this. This object has a :meth:`~defcon.Font.testForExternalChanges` method. This method will compare the data that has been loaded into the font, glyphs, etc. with the data in the UFO on disk. It will report anything that is different from when the UFO was last loaded/saved.

To do this in a relatively effecient way, it stores the modification data and raw text of the UFO file inside the object. When the :meth:`~defcon.Font.testForExternalChanges` method is called, the modification date of the UFO file and the stored modification date are compared. A mismatch between these two will trigger a comparison between the raw text in the UFO file and the stored raw text. This helps cut down on a significant number of false positives.

The :meth:`~defcon.Font.testForExternalChanges` method will return a dictionary describing what could have changed. You can then reload the data as appropriate. The :class:`~defcon.Font` object has a number of *reload* methods specifically for doing this.

Scanning Scheduling
-------------------

defcon does not automatically search for changes, it is up to the application to determine when the scanning should be performed. The scanning can be an expensive operation, so it is best done at key moments when the user *could* have done something outside of your application. A good way to do this is to catch the event in which your application/document has been selected after being inactive.

Caveats
-------

There are a couple of caveats that you should keep in mind:

#. If the object has been modified and an external change has happened, the *object* is considered to be the most current data. External changes will be ignored. *This may change in the future. I'm still thinking this through.*

#. The font and glyph data is loaded only as needed by defcon. This means that the user could have opened a font in your application, looked at some things but not the "X" glyph, switched out of your application, edited the GLIF file for the "X" glyph and switched back into your application. At this point defcon will not notice that the "X" has changed because it has not yet been loaded. This probably doesn't matter as when the "X" is finally loaded the new data will be used. If your application needs to know the exact state of all objects when the font is first created, preload all font and glyph data.