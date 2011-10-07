"""
A set of objects that are suited to being the basis
of font development tools. This works on UFO files.
"""

version = "0.1"

from defcon.errors import DefconError

from defcon.objects.font import Font
from defcon.objects.layerSet import LayerSet
from defcon.objects.layer import Layer
from defcon.objects.glyph import Glyph, addRepresentationFactory, removeRepresentationFactory
from defcon.objects.contour import Contour
from defcon.objects.point import Point
from defcon.objects.component import Component
from defcon.objects.anchor import Anchor
from defcon.objects.info import Info
from defcon.objects.groups import Groups
from defcon.objects.kerning import Kerning
from defcon.objects.features import Features
from defcon.objects.lib import Lib
from defcon.objects.uniData import UnicodeData