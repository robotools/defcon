.. highlight:: python

.. _Subclassing:

===========
Subclassing
===========

The defcon objects are built to have basic functionality. Your application can, and should, have its own functionality that is not part of the standard defcon repertoire. The objects are built with this in mind -- they are built to be subclassed and extended. This is done easily::

  from defcon import Glyph

  class MyCustomGlyph(Glyph):

    def myCustomMethod(self):
      # do something to the glyph data

When it is time to load a font, you pass this custom class to the Font object::

  from defcon import Font

  font = Font(glyphClass=MyCustomGlyph)

When a glyph is loaded, the glyph class you provided will be used to create the glyph object.
