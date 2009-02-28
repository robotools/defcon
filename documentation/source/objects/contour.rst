.. highlight:: python

=======
Contour
=======

.. seealso::

   :ref:`Notifications`:
      The Contour object uses notifications to notify observers of changes.

Tasks
-----

Reference Data
""""""""""""""

* :attr:`~defcon.Contour.bounds`
* :attr:`~defcon.Contour.controlPointBounds`
* :attr:`~defcon.Contour.open`

Direction
"""""""""

* :attr:`~defcon.Contour.clockwise`
* :meth:`~defcon.Contour.reverse`

Points
""""""

* :class:`~defcon.Contour`
* :meth:`~defcon.Contour.index`
* :attr:`~defcon.Contour.onCurvePoints`
* :meth:`~defcon.Contour.setStartPoint`

Segments
""""""""

* :attr:`~defcon.Contour.segments`
* :meth:`~defcon.Contour.removeSegment`
* :meth:`~defcon.Contour.positionForProspectivePointInsertionAtSegmentAndT`
* :meth:`~defcon.Contour.splitAndInsertPointAtSegmentAndT`

Hit Testing
"""""""""""

* :meth:`~defcon.Contour.pointInside`

Drawing
"""""""

* :meth:`~defcon.Contour.draw`
* :meth:`~defcon.Contour.drawPoints`

Changed State
"""""""""""""

* :attr:`~defcon.Contour.dirty`

Notifications
"""""""""""""

* :attr:`~defcon.Contour.dispatcher`
* :meth:`~defcon.Contour.addObserver`
* :meth:`~defcon.Contour.removeObserver`
* :meth:`~defcon.Contour.hasObserver`

Parent
""""""

* :meth:`~defcon.Contour.getParent`
* :meth:`~defcon.Contour.setParent`

Contour
^^^^^^^

.. module:: defcon
.. autoclass:: Contour
   :inherited-members:
   :members:

