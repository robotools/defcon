.. highlight:: python

=========
Component
=========

.. seealso::

   :ref:`Notifications`:
      The Component object uses notifications to notify observers of changes.

Tasks
-----

Reference Data
""""""""""""""

* :attr:`~defcon.Component.bounds`
* :attr:`~defcon.Component.bounds`

Properties
""""""""""

* :attr:`~defcon.Component.baseGlyph`
* :attr:`~defcon.Component.transformation`

Hit Testing
"""""""""""

* :meth:`~defcon.Component.pointInside`

Drawing
"""""""

* :meth:`~defcon.Component.draw`
* :meth:`~defcon.Component.drawPoints`

Changed State
"""""""""""""

* :attr:`~defcon.Component.dirty`

Notifications
"""""""""""""

* :attr:`~defcon.Component.dispatcher`
* :meth:`~defcon.Component.addObserver`
* :meth:`~defcon.Component.removeObserver`
* :meth:`~defcon.Component.hasObserver`

Parent
""""""

* :meth:`~defcon.Component.getParent`
* :meth:`~defcon.Component.setParent`

Component
^^^^^^^^^

.. module:: defcon
.. autoclass:: Component
   :inherited-members:
   :members:
