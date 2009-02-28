.. highlight:: python

=====
Glyph
=====

.. seealso::

  :ref:`Notifications`:
     The Glyph object uses notifications to notify observers of changes.

  :ref:`Representations`:
     The Glyph object can maintain representations of various arbitrary types.

Tasks
-----

Name and Unicodes
"""""""""""""""""

* :attr:`~defcon.Glyph.name`
* :attr:`~defcon.Glyph.unicodes`
* :attr:`~defcon.Glyph.unicode`

Metrics
"""""""

* :attr:`~defcon.Glyph.leftMargin`
* :attr:`~defcon.Glyph.rightMargin`
* :attr:`~defcon.Glyph.width`

Reference Data
""""""""""""""

* :attr:`~defcon.Glyph.bounds`
* :attr:`~defcon.Glyph.controlPointBounds`

General Editing
"""""""""""""""

* :meth:`~defcon.Glyph.clear`
* :meth:`~defcon.Glyph.move`

Contours
""""""""

* :class:`~defcon.Glyph`
* :meth:`~defcon.Glyph.clearContours`
* :meth:`~defcon.Glyph.appendContour`
* :meth:`~defcon.Glyph.insertContour`
* :meth:`~defcon.Glyph.contourIndex`
* :meth:`~defcon.Glyph.autoContourDirection`

Components
""""""""""

* :attr:`~defcon.Glyph.components`
* :meth:`~defcon.Glyph.clearComponents`
* :meth:`~defcon.Glyph.appendComponent`
* :meth:`~defcon.Glyph.componentIndex`
* :meth:`~defcon.Glyph.insertComponent`

Anchors
"""""""

* :attr:`~defcon.Glyph.anchors`
* :meth:`~defcon.Glyph.clearAnchors`
* :meth:`~defcon.Glyph.appendAnchor`
* :meth:`~defcon.Glyph.anchorIndex`
* :meth:`~defcon.Glyph.insertAnchor`

Hit Testing
"""""""""""

* :meth:`~defcon.Contour.pointInside`

Pens and Drawing
""""""""""""""""

* :meth:`~defcon.Glyph.getPen`
* :meth:`~defcon.Glyph.getPointPen`
* :meth:`~defcon.Glyph.draw`
* :meth:`~defcon.Glyph.drawPoints`

Representations
"""""""""""""""

* :meth:`~defcon.Glyph.getRepresentation`
* :meth:`~defcon.Glyph.hasCachedRepresentation`
* :meth:`~defcon.Glyph.representationKeys`
* :meth:`~defcon.Glyph.destroyRepresentation`
* :meth:`~defcon.Glyph.destroyAllRepresentations`

Changed State
"""""""""""""

* :attr:`~defcon.Glyph.dirty`

Notifications
"""""""""""""

* :attr:`~defcon.Glyph.dispatcher`
* :meth:`~defcon.Glyph.addObserver`
* :meth:`~defcon.Glyph.removeObserver`
* :meth:`~defcon.Glyph.hasObserver`

Parent
""""""

* :meth:`~defcon.Glyph.getParent`
* :meth:`~defcon.Glyph.setParent`

Glyph
^^^^^

.. module:: defcon
.. autoclass:: Glyph
   :inherited-members:
   :members:
