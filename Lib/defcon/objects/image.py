from defcon.objects.base import BaseDictObject
from defcon.objects.color import Color


class Image(BaseDictObject):

    changeNotificationName = "Image.Changed"

    def __init__(self, imageDict=None):
        super(Image, self).__init__()
        self["fileName"] = None
        self["xScale"] = 1
        self["xyScale"] = 0
        self["yxScale"] = 0
        self["yScale"] = 1
        self["xOffset"] = 0
        self["yOffset"] = 0
        self["color"] = None
        self._dirty = False
        if imageDict is not None:
            self.update(imageDict)

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
        self.postNotification("Image.FileNameChanged", data=dict(oldFileName=oldFileName, newFileName=fileName))

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
        self.postNotification("Image.TransformationChanged", data=dict(oldTransformation=oldTransformation, newTransformation=transformation))

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
        self.postNotification("Image.ColorChanged", data=dict(old=oldColor, newColor=newColor))

    color = property(_get_color, _set_color, doc="The image's :class:`Color` object. When setting, the value can be a UFO color string, a sequence of (r, g, b, a) or a :class:`Color` object. Setting this posts *Image.ColorChanged* and *Image.Changed* notifications.")


def _test():
    """
    >>> i = Image()
    >>> i.dirty
    False

    >>> i = Image()
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

if __name__ == "__main__":
    import doctest
    doctest.testmod()
