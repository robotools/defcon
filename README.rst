|CI Build Status| |Coverage Status|
|Python Versions| |PyPI Version|

Defcon
======

Defcon is a set of UFO based objects optimized for use in font editing
applications. The objects are built to be lightweight, fast and
flexible. The objects are very bare-bones and they are not meant to be
end-all, be-all objects. Rather, they are meant to provide base
functionality so that you can focus on your application’s behavior, not
object observing or maintaining cached data. Defcon implements UFO3 as
described by the `UFO font format <http://unifiedfontobject.org>`_. If
needed, the
`ufo2-deprecated <https://github.com/typesupply/defcon/tree/ufo2-deprecated>`_
branch has the older, UFO2, version of Defcon.

Install
~~~~~~~

To download and install the latest stable release of defcon from the
`Python Package Index <https://pypi.python.org/pypi/defcon>`_, use the
`pip <https://pip.pypa.io/en/stable/installing/>`_ command line tool:

.. code::

  pip install --upgrade defcon

To install with the `fontPens <https://github.com/robofab-developers/fontPens>`_ package —used for ``Glyph.correctDirection()`` and ``Contour.contourInside()``— do:

.. code::

  pip install --upgrade defcon[pens]

To optionally install defcon with support for `lxml <https://github.com/lxml/lxml>`_,
a faster XML reader and writer library, you can do:

.. code::

  pip install --upgrade defcon[lxml]

You can separate multiple extras using a comma: ``defcon[pens,lxml]``.

Documentation
~~~~~~~~~~~~~

Documentation for Defcon lives at
`defcon.robotools.dev <http://defcon.robotools.dev/en/latest/>`_.

Copyrights
~~~~~~~~~~

This package is distributed under the MIT license. See the
`license <License.txt>`_. Defcon is built in
`Python <http://www.python.org>`_. Parts of RoboFab use
`fontTools <https://github.com/behdad/fonttools>`_, an OpenSource font
toolkit started by Just van Rossum. Parts of Defcon implement the
Property List file format in XML, copyright
`Apple Computer <http://www.apple.com>`_. Parts of Defcon implement tables and
names from PostScript and the OpenType FDK, copyright
`Adobe <http://www.adobe.com>`_.

.. |CI Build Status| image:: https://github.com/robotools/defcon/workflows/Tests/badge.svg
   :target: https://github.com/robotools/defcon/actions?query=workflow%3ATests
.. |Coverage Status| image:: https://coveralls.io/repos/github/robotools/defcon/badge.svg?branch=master
   :target: https://coveralls.io/github/robotools/defcon?branch=master
.. |Python Versions| image:: https://img.shields.io/badge/python-3.7%2C%203.8%2C%203.9%2C%203.10-blue.svg
.. |PyPI Version| image:: https://img.shields.io/pypi/v/defcon.svg
   :target: https://pypi.org/project/defcon/
