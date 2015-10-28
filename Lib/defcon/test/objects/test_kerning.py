import unittest
from defcon.test.testTools import getTestFontPath
from defcon.objects.font import Font


class KerningTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)
        if not hasattr(self, "assertRaisesRegex"):
            self.assertRaisesRegex = self.assertRaisesRegexp

    def test_keys(self):
        font = Font(getTestFontPath())
        self.assertEqual(sorted(font.kerning.keys()),
                         [("A", "A"), ("A", "B")])

    def test_items(self):
        font = Font(getTestFontPath())
        self.assertEqual(sorted(font.kerning.items()),
                         [(("A", "A"), -100), (("A", "B"), 100)])

    def test_values(self):
        font = Font(getTestFontPath())
        self.assertEqual(sorted(font.kerning.values()),
                         [-100, 100])

    def test___contains__(self):
        font = Font(getTestFontPath())
        self.assertIn(("A", "B"), font.kerning)
        self.assertNotIn(("NotInFont", "NotInFont"), font.kerning)

    def test_get(self):
        font = Font(getTestFontPath())
        self.assertEqual(font.kerning.get(("A", "A")), -100)
        self.assertEqual(font.kerning.get(("NotInFont", "NotInFont"), 0), 0)

    def test___getitem__(self):
        font = Font(getTestFontPath())
        self.assertEqual(font.kerning["A", "A"], -100)
        with self.assertRaisesRegex(KeyError, "\('NotInFont', 'NotInFont'\)"):
            font.kerning["NotInFont", "NotInFont"]

    def test___setitem__(self):
        font = Font(getTestFontPath())
        font.kerning["NotInFont", "NotInFont"] = 100
        self.assertEqual(sorted(font.kerning.keys()),
                         [("A", "A"), ("A", "B"), ("NotInFont", "NotInFont")])
        self.assertTrue(font.kerning.dirty)

    def test_clear(self):
        font = Font(getTestFontPath())
        font.kerning.clear()
        self.assertEqual(list(font.kerning.keys()), [])
        self.assertTrue(font.kerning.dirty)

    def test_update(self):
        font = Font(getTestFontPath())
        other = {("X", "X"): 500}
        font.kerning.update(other)
        self.assertEqual(sorted(font.kerning.keys()),
                         [("A", "A"), ("A", "B"), ("X", "X")])
        self.assertTrue(font.kerning.dirty)


if __name__ == "__main__":
    unittest.main()
