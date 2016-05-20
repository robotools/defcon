import unittest
from defcon import Font, Info, Guideline
from defcon.test.testTools import getTestFontPath


class InfoTest(unittest.TestCase):

    def __init__(self, methodName):
        unittest.TestCase.__init__(self, methodName)

    def setUp(self):
        self.font = Font()
        self.info = Info()

    def tearDown(self):
        del self.font

    def test_getParent(self):
        info = self.info
        self.assertIsNone(info.getParent())
        info = Info(self.font)
        self.assertEqual(info.getParent(), self.font)

    def test_font(self):
        info = self.info
        self.assertIsNone(info.font)
        info = Info(self.font)
        self.assertEqual(info.font, self.font)

    def test_guidelines(self):
        info = Info(self.font)
        self.assertEqual(info.guidelines, [])
        guideline1 = Guideline(guidelineDict={"x": 100})
        guideline2 = Guideline(guidelineDict={"y": 200})
        info.guidelines = [guideline1, guideline2]
        self.assertEqual(info.guidelines, [guideline1, guideline2])

    def test_instantiateGuideline(self):
        info = Info(self.font)
        guideline = info.instantiateGuideline()
        self.assertIsInstance(guideline, Guideline)
        guideline = info.instantiateGuideline(guidelineDict={"x": 100})
        self.assertEqual(guideline, {'x': 100})

    def test_beginSelfGuidelineNotificationObservation(self):
        font = self.font
        info = Info(font)
        guideline = info.instantiateGuideline()
        self.assertFalse(guideline.dispatcher.hasObserver(
            info, "Guideline.Changed", guideline))
        info.beginSelfGuidelineNotificationObservation(guideline)
        self.assertTrue(guideline.dispatcher.hasObserver(
            info, "Guideline.Changed", guideline))

    def test_endSelfGuidelineNotificationObservation(self):
        font = self.font
        info = Info(font)
        guideline = info.instantiateGuideline()
        info.beginSelfGuidelineNotificationObservation(guideline)
        self.assertTrue(guideline.hasObserver(
            info, "Guideline.Changed"))
        info.endSelfGuidelineNotificationObservation(guideline)
        self.assertIsNone(guideline.dispatcher)
        self.assertFalse(guideline.hasObserver(
            info, "Guideline.Changed"))

    def test_appendGuideline(self):
        info = Info(self.font)
        guideline1 = Guideline(guidelineDict={"x": 100})
        info.appendGuideline(guideline1)
        self.assertEqual(info.guidelines, [{'x': 100}])
        guideline2 = Guideline(guidelineDict={"y": 200})
        info.appendGuideline(guideline2)
        self.assertEqual(info.guidelines, [{'x': 100}, {'y': 200}])
        guideline3 = Guideline(guidelineDict={"y": 100})
        info.appendGuideline(guideline3)
        self.assertEqual(info.guidelines, [{'x': 100}, {'y': 200}, {'y': 100}])

    def test_insertGuideline(self):
        info = Info(self.font)
        guideline1 = Guideline(guidelineDict={"x": 100})
        info.insertGuideline(0, guideline1)
        self.assertEqual(info.guidelines, [{'x': 100}])
        guideline2 = Guideline(guidelineDict={"y": 200})
        info.insertGuideline(0, guideline2)
        self.assertEqual(info.guidelines, [{'y': 200}, {'x': 100}])
        guideline3 = Guideline(guidelineDict={"y": 100})
        info.insertGuideline(2, guideline3)
        self.assertEqual(info.guidelines, [{'y': 200}, {'x': 100}, {'y': 100}])

    def test_removeGuideline(self):
        info = Info(self.font)
        guideline1 = Guideline(guidelineDict={"x": 100})
        guideline2 = Guideline(guidelineDict={"y": 200})
        info.guidelines = [guideline1, guideline2]
        info.removeGuideline(guideline1)
        self.assertEqual(info.guidelines, [guideline2])

    def test_guidelineIndex(self):
        info = Info(self.font)
        guideline1 = Guideline(guidelineDict={"x": 100})
        guideline2 = Guideline(guidelineDict={"y": 200})
        info.guidelines = [guideline1, guideline2]
        self.assertEqual(info.guidelineIndex(guideline1), 0)
        self.assertEqual(info.guidelineIndex(guideline2), 1)

    def test_clearGuidelines(self):
        info = Info(self.font)
        guideline1 = Guideline(guidelineDict={"x": 100})
        guideline2 = Guideline(guidelineDict={"y": 200})
        info.guidelines = [guideline1, guideline2]
        self.assertEqual(info.guidelines, [guideline1, guideline2])
        info.clearGuidelines()
        self.assertEqual(info.guidelines, [])

    def test_endSelfNotificationObservation(self):
        font = self.font
        info = Info(font)
        self.assertIsNotNone(info.dispatcher)
        info.endSelfNotificationObservation()
        self.assertIsNone(info.dispatcher)
        self.assertIsNone(info.font)


if __name__ == "__main__":
    unittest.main()
