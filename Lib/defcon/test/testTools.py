import os
import shutil

def getTestFontPath(fileName='TestFont.ufo'):
    testDirectory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), 'testData')
    return os.path.join(testDirectory, fileName)

def getTestFontCopyPath(testFontPath=None):
    if testFontPath is None:
        testFontPath = getTestFontPath()
    dirName, fileName = os.path.split(testFontPath)
    fileName = os.path.splitext(fileName)[0] + 'Copy.ufo'
    return os.path.join(dirName, fileName)

def makeTestFontCopy(testFontPath=None):
    if testFontPath is None:
        testFontPath = getTestFontPath()
    copyPath = getTestFontCopyPath(testFontPath)
    shutil.copytree(testFontPath, copyPath)
    return copyPath

def tearDownTestFontCopy(testFontPath=None):
    if testFontPath is None:
        testFontPath = getTestFontCopyPath()
    shutil.rmtree(testFontPath)

class NotificationTestObject(object):
    
    def testCallback(self, notification):
        print notification.name, notification.data