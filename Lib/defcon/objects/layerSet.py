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
        self._defaultLayer = layer
        self.postNotification(notification="LayerSet.DefaultLayerChanged")
        self.dirty = True

    defaultLayer = property(_get_defaultLayer, _set_defaultLayer, doc="The default :class:`Layer` object. Setting this will post a \"LayerSet.DefaultLayerChanged\" notification as well as the standard change notification.")

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

    layerOrder = property(_get_layerOrder, _set_layerOrder, doc="The layer order from top to bottom. Setting this will post a \"LayerSet.LayerOrderChanged\" notification as well as the standard change notification.")

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

    def newLayer(self, name, glyphSet=None):
        """
        Create a new :class:`Layer` and add it to
        the top of the layer order. **glyphSet** should
        only be passed when reading from a UFO.
        """
        if name in self._layers:
            raise KeyError("A layer named \"%s\" already exists." % name)
        layer = self._instantiateLayerObject(glyphSet)
        layer.setParent(self)
        self._layers[name] = layer
        self._layerOrder.insert(0, name)
        self.dirty = True
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