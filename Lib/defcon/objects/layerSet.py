from defcon.objects.base import BaseObject
from defcon.objects.layer import Layer


class LayerSet(BaseObject):

    changeNotificationName = "LayerSet.Changed"

    def __init__(self, layerClass=None, libClass=None, unicodeDataClass=None, glyphClass=None,
            glyphContourClass=None, glyphPointClass=None, glyphComponentClass=None, glyphAnchorClass=None):
        super(LayerSet, self).__init__()
        if layerClass is None:
            layerClass = Layer

        self._layerClass = layerClass
        self._libClass = libClass
        self._unicodeDataClass = unicodeDataClass
        self._glyphClass = glyphClass
        self._glyphContourClass = glyphContourClass
        self._glyphPointClass = glyphPointClass
        self._glyphComponentClass = glyphComponentClass
        self._glyphAnchorClass = glyphAnchorClass

        self._layers = {}
        self._layerOrder = []
        self._defaultLayer = None

        self._renamedLayers = {}
        self._scheduledForDeletion = set()

    def _get_defaultLayerName(self):
        defaultLayer = self.defaultLayer
        for name, layer in self._layers.items():
            if layer == defaultLayer:
                return name

    _defaultLayerName = property(_get_defaultLayerName)

    def _get_defaultLayer(self):
        return self._defaultLayer

    def _set_defaultLayer(self, layer):
        if layer is None:
            raise ValueError("The default layer must not be None.")
        if layer == self._defaultLayer:
            return
        if layer.name is None:
            layer.name = "public.default"
        self._defaultLayer = layer
        self.postNotification(notification="LayerSet.DefaultLayerChanged")
        self.dirty = True

    defaultLayer = property(_get_defaultLayer, _set_defaultLayer, doc="The default :class:`Layer` object. Setting this will post *LayerSet.DefaultLayerChanged* and *LayerSet.Changed* notifications.")

    def _get_layerOrder(self):
        return list(self._layerOrder)

    def _set_layerOrder(self, order):
        if self._layerOrder == order:
            return
        assert len(order) == len(self._layerOrder)
        assert set(order) == set(self._layerOrder)
        self._layerOrder = list(order)
        self.postNotification(notification="LayerSet.LayerOrderChanged")
        self.dirty = True

    layerOrder = property(_get_layerOrder, _set_layerOrder, doc="The layer order from top to bottom. Setting this will post *LayerSet.LayerOrderChanged* and *LayerSet.Changed* notifications.")

    # -------------
    # Dict Behavior
    # -------------

    def _instantiateLayerObject(self, glyphSet):
        layer = self._layerClass(
            libClass=self._libClass,
            unicodeDataClass=self._unicodeDataClass,
            glyphClass=self._glyphClass,
            glyphContourClass=self._glyphContourClass,
            glyphPointClass=self._glyphPointClass,
            glyphComponentClass=self._glyphComponentClass,
            glyphAnchorClass=self._glyphAnchorClass,
        )
        return layer

    def _setParentDataInLayer(self, layer):
        layer.setParent(self)
        layer.dispatcher = self.dispatcher
        layer.addObserver(observer=self, methodName="_layerDirtyStateChange", notification="Layer.Changed")
        layer.addObserver(observer=self, methodName="_layerNameChange", notification="Layer.NameChanged")

    def _removeParentDataInLayer(self, layer):
        layer.setParent()
        layer.removeObserver(observer=self, notification="Layer.Changed")
        layer.removeObserver(observer=self, notification="Layer.NameChanged")
        layer.dispatcher = None

    def newLayer(self, name, glyphSet=None):
        """
        Create a new :class:`Layer` and add it to
        the top of the layer order. **glyphSet** should
        only be passed when reading from a UFO.
        """
        if name in self._layers:
            raise KeyError("A layer named \"%s\" already exists." % name)
        layer = self._instantiateLayerObject(glyphSet)
        layer.name = name
        self._setParentDataInLayer(layer)
        if glyphSet is None:
            layer.dirty = True
        self._layers[name] = layer
        self._layerOrder.insert(0, name)
        return layer

    def __iter__(self):
        names = self.layerOrder
        while names:
            name = names[0]
            yield self[name]
            names = names[1:]

    def __getitem__(self, name):
        if name is None:
            name = self._defaultLayerName
        return self._layers[name]

    def __delitem__(self, name):
        if name is None:
            name = self._defaultLayerName
        if name not in self:
            raise KeyError("%s not in layers" % name)
        del self._layers[name]
        self._layerOrder.remove(name)
        self._scheduledForDeletion.add(name)
        self.postNotification("LayerSet.DeletedLayer", data=name)
        self.dirty = True

    def __len__(self):
        return len(self.layerOrder)

    def __contains__(self, name):
        if name is None:
            name = self._defaultLayerName
        return name in self._layers

    # ----------------------
    # Notification Callbacks
    # ----------------------

    def _layerDirtyStateChange(self, notification):
        if notification.object.dirty:
            self.dirty = True

    def _layerNameChange(self, notification):
        data = notification.data
        oldName = data["oldName"]
        newName = data["newName"]
        self._layers[newName] = self._layers.pop(oldName)
        index = self._layerOrder.index(oldName)
        self._layerOrder.pop(index)
        self._layerOrder.insert(index, newName)


# -----
# Tests
# -----

def _testSetParentDataInLayer():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> layer = font.layers[None]
    >>> id(layer.getParent()) == id(layers)
    True
    """

def _testLayerOrder():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> layers.layerOrder
    ['Layer 1', 'public.background', 'public.default']
    >>> layers.layerOrder = list(reversed(layers.layerOrder))
    >>> layers.layerOrder
    ['public.default', 'public.background', 'Layer 1']
    """

def _testDefaultLayer():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> layer = layers.defaultLayer
    >>> layer == layers["public.default"]
    True
    >>> layer = layers["Layer 1"]
    >>> layers.defaultLayer = layer
    >>> layer == layers.defaultLayer
    True
    """

def _testNewLayer():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> layer = font.newLayer("Test")
    >>> layer.dirty
    True
    >>> layers.dirty
    True
    >>> font.dirty
    True
    >>> layers.layerOrder
    ['Test', 'Layer 1', 'public.background', 'public.default']
    """

def _testIter():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> [layer.name for layer in layers]
    ['Layer 1', 'public.background', 'public.default']
    """

def _testGetitem():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> layers["public.default"].name
    'public.default'
    """

def _testDelItem():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> font = Font(makeTestFontCopy())
    >>> layers = font.layers
    >>> del layers["public.background"]
    >>> layers.dirty = True
    >>> layers.layerOrder
    ['Layer 1', 'public.default']
    >>> "public.background" in layers
    False
    >>> len(layers)
    2
    >>> layers["public.background"]
    Traceback (most recent call last):
        ...
    KeyError: 'public.background'
    >>> font.save()
    "XXX Make sure it is gone."
    >>> tearDownTestFontCopy()

    Maybe test that deleting a lyer, then making a new layer
    with the same name doesn't result in the old layer remaining
    after save.
    """

def _testLen():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> len(layers)
    3

    >>> font = Font()
    >>> layers = font.layers
    >>> len(layers)
    1
    """

def _testContains():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> 'public.default' in layers
    True
    >>> 'NotInFont' in layers
    False
    """

def _testGlyphNameChange():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> layer = layers["public.background"]
    >>> layers.dirty = False
    >>> layer.dirty = False
    >>> layer.name = "Name Change Test"
    >>> layers.layerOrder
    ['Layer 1', 'Name Change Test', 'public.default']
    >>> layer.dirty
    True
    >>> layers.dirty
    True
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
