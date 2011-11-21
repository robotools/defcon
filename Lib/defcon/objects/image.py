from defcon.objects.base import BaseDictObject
from defcon.objects.color import Color

_defaultTransformation = {
    "xScale"  : 1,
    "xyScale" : 0,
    "yxScale" : 0,
    "yScale"  : 1,
    "xOffset" : 0,
    "yOffset" : 0
}


class Image(BaseDictObject):

    """
    This object represents an image reference in a glyph.

    **This object posts the following notifications:**

    ===========================
    Name
    ===========================
    Image.Changed
    Image.FileNameChanged
    Image.TransformationChanged
    Image.ColorChanged
    ===========================

    During initialization an image dictionary, following the format defined
    in the UFO spec, can be passed. If so, the new object will be populated
    with the data from the dictionary.
    """

    changeNotificationName = "Image.Changed"
    representationFactories = {}

    def __init__(self, imageDict=None):
        super(Image, self).__init__()
        self["fileName"] = None
        self["color"] = None
        if imageDict is not None:
            self.update(imageDict)
        for key, value in _defaultTransformation.items():
            if self.get(key) is None:
                self[key] = value
        self._dirty = False

    # ----------
    # Properties
    # ----------

    def _get_fileName(self):
        return self["fileName"]

    def _set_fileName(self, fileName):
        oldFileName = self.get("fileName")
        if fileName == oldFileName:
            return
        self["fileName"] = fileName
        self.postNotification("Image.FileNameChanged", data=dict(oldValue=oldFileName, newValue=fileName))

    fileName = property(_get_fileName, _set_fileName, doc="The file name the image. Setting this will posts *Image.Changed* and *Image.FileNameChanged* notifications.")

    def _get_transformation(self):
        if "xScale" not in self:
            return
        return (self["xScale"], self["xyScale"], self["yxScale"], self["yScale"], self["xOffset"], self["yOffset"])

    def _set_transformation(self, transformation):
        oldTransformation = self.transformation
        if oldTransformation == transformation:
            return
        xScale, xyScale, yxScale, yScale, xOffset, yOffset = transformation
        # hold the notifications so that only one is sent out
        self.holdNotifications()
        self["xScale"] = xScale
        self["xyScale"] = xyScale
        self["yxScale"] = yxScale
        self["yScale"] = yScale
        self["xOffset"] = xOffset
        self["yOffset"] = yOffset
        self.releaseHeldNotifications()
        self.postNotification("Image.TransformationChanged", data=dict(oldValue=oldTransformation, newValue=transformation))

    transformation = property(_get_transformation, _set_transformation, doc="The transformation matrix for the image. Setting this will posts *Image.Changed* and *Image.TransformationChanged* notifications.")

    def _get_color(self):
        return self.get("color")

    def _set_color(self, color):
        if color is None:
            newColor = None
        else:
            newColor = Color(color)
        oldColor = self.get("color")
        if newColor == oldColor:
            return
        self["color"] = newColor
        self.postNotification("Image.ColorChanged", data=dict(oldValue=oldColor, newValue=newColor))

    color = property(_get_color, _set_color, doc="The image's :class:`Color` object. When setting, the value can be a UFO color string, a sequence of (r, g, b, a) or a :class:`Color` object. Setting this posts *Image.ColorChanged* and *Image.Changed* notifications.")


def _testAttributes():
    """
    >>> i = Image()
    >>> i.dirty
    False

    >>> i.fileName = "foo"
    >>> i.fileName
    'foo'
    >>> i.dirty
    True

    >>> i = Image()
    >>> i.transformation = (1, 2, 3, 4, 5, 6)
    >>> i.transformation
    (1, 2, 3, 4, 5, 6)
    >>> i.dirty
    True

    >>> i = Image()
    >>> i.color = "1, 1, 1, 1"
    >>> i.color
    '1,1,1,1'
    >>> i.dirty
    True

    >>> i = Image(dict(fileName="foo.png", xScale="1", xyScale="2", yxScale="3", yScale="4", xOffset="5", yOffset="6", color="0,0,0,0"))
    >>> i.fileName, i.transformation, i.color
    ('foo.png', ('1', '2', '3', '4', '5', '6'), '0,0,0,0')
    """

def _testRead():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> glyph = font.layers["Layer 1"]["A"]
    >>> image = glyph.image
    >>> image.fileName
    'image 1.png'
    >>> image.color
    '0.1,0.2,0.3,0.4'
    >>> image.transformation
    (0.5, 0, 0, 0.5, 0, 0)
    """

def _testWrite():
    """
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> from defcon import Font
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> glyph = font.layers[None]["A"]
    >>> glyph.image = Image()
    >>> glyph.image.color = "1,1,1,1"
    >>> glyph.image.fileName = "foo.png"
    >>> glyph.image.transformation = (1, 2, 3, 4, 5, 6)
    >>> font.save()
    >>> font = Font(path)
    >>> glyph = font.layers[None]["A"]
    >>> sorted(glyph.image.items())
    [('color', '1,1,1,1'), ('fileName', 'foo.png'), ('xOffset', 5), ('xScale', 1), ('xyScale', 2), ('yOffset', 6), ('yScale', 4), ('yxScale', 3)]
    >>> tearDownTestFontCopy()
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
