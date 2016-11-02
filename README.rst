|Travis Build Status| |Appveyor Build Status| |Coverage Status|
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

Documentation
~~~~~~~~~~~~~

Documentation for Defcon lives at
`ts-defcon.readthedocs.io <http://ts-defcon.readthedocs.io/en/latest/>`_.

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

.. |Travis Build Status| image:: https://travis-ci.org/typesupply/defcon.svg?branch=master
   :target: https://travis-ci.org/typesupply/defcon
.. |Appveyor Build Status| image:: https://ci.appveyor.com/api/projects/status/github/typesupply/defcon?branch=master&svg=true
   :target: https://ci.appveyor.com/project/typesupply/defcon/branch/master
.. |Coverage Status| image:: https://coveralls.io/repos/github/typesupply/defcon/badge.svg?branch=master
   :target: https://coveralls.io/github/typesupply/defcon?branch=master
.. |Python Versions| image:: https://img.shields.io/badge/python-2.7%2C%203.5-blue.svg
.. |PyPI Version| image:: https://img.shields.io/pypi/v/defcon.svg
   :target: https://pypi.org/project/defcon/
