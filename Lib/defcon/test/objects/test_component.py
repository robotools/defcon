import unittest
from defcon import Component, Glyph


class ComponentTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def setUp(self):
        glyph = Glyph()
        component = Component()
        glyph.appendComponent(component)
        self.glyph = glyph
        self.component = component

    def tearDown(self):
        del self.component
        del self.glyph

    def test_getParent(self):
        self.assertEqual(self.component.getParent(), self.glyph)

    def test_identifier(self):
        self.component.identifier = "component 1"
        self.assertEqual(self.component.identifier, "component 1")

    def test_identifiers(self):
        self.component.identifier = "component 1"
        self.assertEqual(sorted(self.glyph.identifiers), ["component 1"])

    def test_duplicate_identifier_error(self):
        glyph = self.glyph
        component = self.component
        component.identifier = "component 1"
        self.assertEqual(component.identifier, "component 1")
        component = Component(glyph)
        with self.assertRaises(AssertionError):
            component.identifier = "component 1"
        component.identifier = "component 2"
        self.assertEqual(sorted(glyph.identifiers),
                         ["component 1", "component 2"])
        component.identifier = "not component 2 anymore"
        self.assertEqual(component.identifier,
                         "not component 2 anymore")
        self.assertEqual(sorted(glyph.identifiers),
                         ["component 1", "not component 2 anymore"])
        component.identifier = None
        self.assertEqual(sorted(glyph.identifiers),
                         ["component 1"])


if __name__ == "__main__":
    unittest.main()
