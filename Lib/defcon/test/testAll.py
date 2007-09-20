import unittest
import doctest
from defcon.objects import base
from defcon.objects import font
from defcon.objects import glyph
from defcon.objects import contour
from defcon.objects import point
from defcon.objects import component
from defcon.objects import anchor
from defcon.objects import lib
from defcon.objects import kerning
from defcon.objects import info
from defcon.objects import groups

test = [
    # commented modules have no tests
    base,
    font,
    glyph,
    contour,
    # point,
    # component,
    # anchor,
    # lib,
    kerning,
    # info,
    # groups
]

suite = unittest.TestSuite()
for mod in test:
    suite.addTest(doctest.DocTestSuite(mod))
runner = unittest.TextTestRunner()
runner.run(suite)