.. highlight:: python

====
Font
====

.. seealso::

   :ref:`Notifications`:
      The Font object uses notifications to notify observers of changes.

   :ref:`External Changes<External_Changes>`:
      The Font object can observe the files within the UFO for external modifications.

Tasks
-----

File Operations
"""""""""""""""

* :class:`~defcon.Font`
* :meth:`~defcon.Font.save`
* :attr:`~defcon.Font.path`
* :attr:`~defcon.Font.ufoFormatVersion`
* :meth:`~defcon.Font.testForExternalChanges`
* :meth:`~defcon.Font.reloadInfo`
* :meth:`~defcon.Font.reloadKerning`
* :meth:`~defcon.Font.reloadGroups`
* :meth:`~defcon.Font.reloadFeatures`
* :meth:`~defcon.Font.reloadLib`

Sub-Objects
"""""""""""

* :attr:`~defcon.Font.info`
* :attr:`~defcon.Font.kerning`
* :attr:`~defcon.Font.groups`
* :attr:`~defcon.Font.features`
* :attr:`~defcon.Font.layers`
* :attr:`~defcon.Font.lib`
* :attr:`~defcon.Font.unicodeData`

Glyphs
""""""

* :class:`~defcon.Font`
* :meth:`~defcon.Font.newGlyph`
* :meth:`~defcon.Font.insertGlyph`
* :meth:`~defcon.Font.keys`

Layers
""""""
* :meth:`~defcon.Font.newLayer`


Reference Data
""""""""""""""

* :attr:`~defcon.Font.glyphsWithOutlines`
* :attr:`~defcon.Font.componentReferences`
* :attr:`~defcon.Font.bounds`
* :attr:`~defcon.Font.controlPointBounds`

Changed State
"""""""""""""

* :attr:`~defcon.Font.dirty`

Notifications
"""""""""""""

* :attr:`~defcon.Font.dispatcher`
* :meth:`~defcon.Font.addObserver`
* :meth:`~defcon.Font.removeObserver`
* :meth:`~defcon.Font.hasObserver`


Font
^^^^

.. module:: defcon
.. autoclass:: Font
   :inherited-members:
   :members:

