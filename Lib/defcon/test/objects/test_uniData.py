import unittest
from defcon.objects.font import Font
from defcon.test.testTools import getTestFontPath


class UnicodeDataTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def test_removeGlyphData(self):
        path = getTestFontPath()
        font = Font(path)
        font.newGlyph("XXX")
        font.unicodeData.addGlyphData("XXX", [65])
        font.unicodeData.removeGlyphData("A", [65])
        self.assertEqual(font.unicodeData[65], ['XXX'])

    def test_addGlyphData(self):
        path = getTestFontPath()
        font = Font(path)
        font.newGlyph("XXX")
        font.unicodeData.addGlyphData("XXX", [1000])
        self.assertEqual(font.unicodeData[1000], ['XXX'])
        font.unicodeData.addGlyphData("XXX", [65])
        self.assertEqual(font.unicodeData[65], ['A', 'XXX'])

    def test_delitem(self):
        path = getTestFontPath()
        font = Font(path)
        del font.unicodeData[65]
        self.assertNotIn(65, font.unicodeData)
        font.unicodeData.glyphNameForUnicode(65)

        self.assertNotIn(0xBEAF, font.unicodeData)
        del font.unicodeData[0xBEAF]
        self.assertNotIn(0xBEAF, font.unicodeData)

    def test_setitem(self):
        path = getTestFontPath()
        font = Font(path)
        font.newGlyph("XXX")
        font.unicodeData[1000] = ["XXX"]
        self.assertEqual(font.unicodeData[1000], ['XXX'])
        font.unicodeData[65] = ["YYY"]
        self.assertEqual(font.unicodeData[65], ['A', 'YYY'])

    def test_unicodeForGlyphName(self):
        path = getTestFontPath()
        font = Font(path)
        self.assertEqual(font.unicodeData.unicodeForGlyphName("A"), 65)

    def test_glyphNameForUnicode(self):
        path = getTestFontPath()
        font = Font(path)
        self.assertEqual(font.unicodeData.glyphNameForUnicode(65), 'A')

    def test_pseudoUnicodeForGlyphName(self):
        path = getTestFontPath()
        font = Font(path)
        self.assertEqual(font.unicodeData.pseudoUnicodeForGlyphName("A"), 65)
        font.newGlyph("A.foo")
        self.assertEqual(font.unicodeData.pseudoUnicodeForGlyphName("A.foo"),
                         65)
        font.newGlyph("B_A")
        self.assertEqual(font.unicodeData.pseudoUnicodeForGlyphName("B_A"), 66)

    def test_scriptForGlyphName(self):
        path = getTestFontPath()
        font = Font(path)
        font.newGlyph("A.alt")
        self.assertEqual(font.unicodeData.scriptForGlyphName("A"), 'Latin')
        self.assertEqual(font.unicodeData.scriptForGlyphName("A.alt"), 'Latin')
        self.assertEqual(font.unicodeData.scriptForGlyphName("A.alt", False),
                         'Unknown')
        font.newGlyph("Alpha")
        font["Alpha"].unicode = 0x0391
        self.assertEqual(font.unicodeData.scriptForGlyphName("Alpha"), 'Greek')

    def test_blockForGlyphName(self):
        path = getTestFontPath()
        font = Font(path)
        font.newGlyph("A.alt")
        self.assertEqual(font.unicodeData.blockForGlyphName("A"),
                         'Basic Latin')
        self.assertEqual(font.unicodeData.blockForGlyphName("A.alt"),
                         'Basic Latin')
        self.assertEqual(font.unicodeData.blockForGlyphName("A.alt", False),
                         'No_Block')
        font.newGlyph("schwa")
        font["schwa"].unicode = 0x0259
        self.assertEqual(font.unicodeData.blockForGlyphName("schwa"),
                         'IPA Extensions')

    def test_categoryForGlyphName(self):
        path = getTestFontPath()
        font = Font(path)
        font.newGlyph("A.alt")
        self.assertEqual(font.unicodeData.categoryForGlyphName("A"), 'Lu')
        self.assertEqual(font.unicodeData.categoryForGlyphName("A.alt"), 'Lu')
        self.assertEqual(font.unicodeData.categoryForGlyphName("A.alt", False),
                         'Cn')

    def test_decompositionBaseForGlyphName(self):
        path = getTestFontPath()
        font = Font(path)
        font.newGlyph("Aacute")
        font["Aacute"].unicode = int("00C1", 16)
        self.assertEqual(
            font.unicodeData.decompositionBaseForGlyphName("Aacute", True),
            'A')
        font.newGlyph("Aringacute")
        font["Aringacute"].unicode = int("01FA", 16)
        self.assertEqual(
            font.unicodeData.decompositionBaseForGlyphName("Aringacute", True),
            'A')
        font.newGlyph("Aacute.alt")
        self.assertEqual(
            font.unicodeData.decompositionBaseForGlyphName("Aacute.alt", True),
            'A')
        font.newGlyph("A.alt")
        self.assertEqual(
            font.unicodeData.decompositionBaseForGlyphName("Aacute.alt", True),
            'A.alt')

    def test_closeRelativeForGlyphName(self):
        font = Font()
        font.newGlyph("parenleft")
        font["parenleft"].unicode = int("0028", 16)
        font.newGlyph("parenright")
        font["parenright"].unicode = int("0029", 16)
        font.newGlyph("parenleft.alt")
        font.newGlyph("parenright.alt")
        self.assertEqual(
            font.unicodeData.closeRelativeForGlyphName("parenleft", True),
            'parenright')
        self.assertEqual(
            font.unicodeData.closeRelativeForGlyphName("parenleft.alt", True),
            'parenright.alt')
        del font["parenright.alt"]
        self.assertEqual(
            font.unicodeData.closeRelativeForGlyphName("parenleft.alt", True),
            'parenright')

    def test_openRelativeForGlyphName(self):
        font = Font()
        font.newGlyph("parenleft")
        font["parenleft"].unicode = int("0028", 16)
        font.newGlyph("parenright")
        font["parenright"].unicode = int("0029", 16)
        font.newGlyph("parenleft.alt")
        font.newGlyph("parenright.alt")
        self.assertEqual(
            font.unicodeData.openRelativeForGlyphName("parenright", True),
            'parenleft')
        self.assertEqual(
            font.unicodeData.openRelativeForGlyphName("parenright.alt", True),
            'parenleft.alt')
        del font["parenleft.alt"]
        self.assertEqual(
            font.unicodeData.openRelativeForGlyphName("parenright.alt", True),
            'parenleft')


if __name__ == "__main__":
    unittest.main()
