import unittest
from defcon.objects.anchor import Anchor
from defcon.objects.font import Font


class AnchorTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def setUp(self):
        self.font = Font()
        self.glyph = self.font.newGlyph("A")
        self.anchor = Anchor()

    def tearDown(self):
        del self.anchor
        del self.glyph
        del self.font

    def test_dirty(self):
        self.assertFalse(self.anchor.dirty)
        notdirty = not self.anchor.dirty
        self.anchor.dirty = notdirty
        self.assertEqual(self.anchor.dirty, notdirty)
        self.anchor.dirty = not notdirty
        self.assertNotEqual(self.anchor.dirty, notdirty)

    def test_x(self):
        self.anchor.x = 100
        self.assertEqual(self.anchor.x, 100)
        self.assertTrue(self.anchor.dirty)

    def test_y(self):
        self.anchor.y = 100
        self.assertEqual(self.anchor.y, 100)
        self.assertTrue(self.anchor.dirty)

    def test_name(self):
        self.anchor.name = "foo"
        self.assertEqual(self.anchor.name, "foo")
        self.assertTrue(self.anchor.dirty)
        self.anchor.name = None
        self.assertIsNone(self.anchor.name)
        self.assertTrue(self.anchor.dirty)

    def test_color(self):
        self.anchor.color = "1,1,1,1"
        self.assertEqual(self.anchor.color, "1,1,1,1")
        self.assertTrue(self.anchor.dirty)

    def test_identifier(self):
        self.assertIsNone(self.anchor.identifier)
        self.anchor.generateIdentifier()
        self.assertIsNotNone(self.anchor.identifier)
        self.anchor.identifier = "foo"
        self.assertEqual(self.anchor.identifier, "foo")

    def test_instance(self):
        a = Anchor(anchorDict=dict(x=1, y=2, name="3", identifier="4",
                                   color="1,1,1,1"))
        self.assertEqual((a.x, a.y, a.name, a.identifier, a.color),
                         (1, 2, "3", "4", "1,1,1,1"))


if __name__ == "__main__":
    unittest.main()
