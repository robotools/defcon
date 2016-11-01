from __future__ import print_function
import os
import shutil
from pkg_resources import resource_filename


TESTDATA_DIR = resource_filename("defcon.test", 'testdata')


def getTestFontPath(fileName='TestFont.ufo'):
    return os.path.join(TESTDATA_DIR, fileName)


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


class NotificationTestObserver(object):

    def __init__(self):
        self.stack = []

    def notificationCallback(self, notification):
        print(notification.name, notification.object.name)
        self.stack.append((notification.name, notification.object.name))

    def testCallback(self, notification):
        print(notification.name, notification.data)
