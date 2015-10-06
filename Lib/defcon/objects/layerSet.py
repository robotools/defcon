import weakref
from ufoLib import UFOReader
from defcon.objects.base import BaseObject
from defcon.objects.layer import Layer


class LayerSet(BaseObject):

    """
    This object manages all layers in the font.

    **This object posts the following notifications:**

    ============================
    Name
    ============================
    LayerSet.Changed
    LayerSet.LayersChanged
    LayerSet.LayerChanged
    LayerSet.DefaultLayerChanged
    LayerSet.LayerOrderChanged
    LayerSet.LayerAdded
    LayerSet.LayerDeleted
    LayerSet.LayerWillBeDeleted
    ============================

    This object behaves like a dict. For example, to get a particular
    layer::

        layer = layerSet["layer name"]

    If the layer name is None, the default layer will be retrieved.

    Note: It's up to the caller to ensure that a default layer is present
    as required by the UFO specification.
    """

    changeNotificationName = "LayerSet.Changed"
    representationFactories = {}

    def __init__(self, font=None, layerClass=None, libClass=None, unicodeDataClass=None,
            guidelineClass=None, glyphClass=None,
            glyphContourClass=None, glyphPointClass=None, glyphComponentClass=None, glyphAnchorClass=None,
            glyphImageClass=None):

        if font is not None:
            font = weakref.ref(font)
        self._font = font
        super(LayerSet, self).__init__()
        self.beginSelfNotificationObservation()

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
        self._glyphImageClass = glyphImageClass
        self._guidelineClass = guidelineClass

        self._layers = {}
        self._layerOrder = []
        self._defaultLayer = None

        self._layerActionHistory = []

    def __del__(self):
        super(LayerSet, self).__del__()
        self._layers = None

    # --------------
    # Parent Objects
    # --------------

    def getParent(self):
        return self.font

    def _get_font(self):
        if self._font is None:
            return None
        return self._font()

    font = property(_get_font, doc="The :class:`Font` that this layer set belongs to.")

    # -------------
    # Default Layer
    # -------------

    def _get_defaultLayerName(self):
        defaultLayer = self.defaultLayer
        for name, layer in list(self._layers.items()):
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
        oldName = None
        if self._defaultLayer is not None:
            oldName = self._defaultLayer.name
        self._defaultLayer = layer
        self._layerActionHistory.append(dict(action="default", newDefault=layer.name, oldDefault=oldName))
        self.postNotification(notification="LayerSet.DefaultLayerChanged", data=dict(oldValue=oldName, newValue=layer.name))
        self.dirty = True

    defaultLayer = property(_get_defaultLayer, _set_defaultLayer, doc="The default :class:`Layer` object. Setting this will post *LayerSet.DefaultLayerChanged* and *LayerSet.Changed* notifications.")

    # -----------
    # Layer Order
    # -----------

    def _get_layerOrder(self):
        return list(self._layerOrder)

    def _set_layerOrder(self, order):
        oldOrder = self._layerOrder
        if self._layerOrder == order:
            return
        assert len(order) == len(self._layerOrder)
        assert set(order) == set(self._layerOrder)
        self._layerOrder = list(order)
        self.postNotification(notification="LayerSet.LayerOrderChanged", data=dict(oldValue=oldOrder, newValue=order))
        self.dirty = True

    layerOrder = property(_get_layerOrder, _set_layerOrder, doc="The layer order from top to bottom. Setting this will post *LayerSet.LayerOrderChanged* and *LayerSet.Changed* notifications.")

    # -------------
    # Layer Creation
    # -------------

    def instantiateLayer(self, glyphSet):
        layer = self._layerClass(
            layerSet=self,
            glyphSet=glyphSet,
            libClass=self._libClass,
            unicodeDataClass=self._unicodeDataClass,
            glyphClass=self._glyphClass,
            glyphContourClass=self._glyphContourClass,
            glyphPointClass=self._glyphPointClass,
            glyphComponentClass=self._glyphComponentClass,
            glyphAnchorClass=self._glyphAnchorClass,
            guidelineClass=self._guidelineClass,
            glyphImageClass=self._glyphImageClass
        )
        return layer

    def beginSelfLayerNotificationObservation(self, layer):
        layer.addObserver(observer=self, methodName="_layerDirtyStateChange", notification="Layer.Changed")
        layer.addObserver(observer=self, methodName="_layerNameChange", notification="Layer.NameChanged")

    def endSelfLayerNotificationObservation(self, layer):
        if layer.dispatcher is None:
            return
        layer.removeObserver(observer=self, notification="Layer.Changed")
        layer.removeObserver(observer=self, notification="Layer.NameChanged")
        layer.endSelfNotificationObservation()

    def newLayer(self, name, glyphSet=None):
        """
        Create a new :class:`Layer` and add it to
        the top of the layer order. **glyphSet** should
        only be passed when reading from a UFO.

        This posts *LayerSet.LayerAdded* and *LayerSet.Changed* notifications.
        """
        if name in self._layers:
            raise KeyError("A layer named \"%s\" already exists." % name)
        assert name is not None
        layer = self.instantiateLayer(glyphSet)
        self.beginSelfLayerNotificationObservation(layer)
        layer.disableNotifications()
        layer.name = name
        if glyphSet is None:
            layer.dirty = True
        else:
            glyphSet.readLayerInfo(layer)
            layer.dirty = False
        layer.enableNotifications()
        self._stampLayerInfoDataState(layer)
        self._layers[name] = layer
        self._layerOrder.append(name)
        self._layerActionHistory.append(dict(action="new", name=name))
        self.postNotification("LayerSet.LayerAdded", data=dict(name=name))
        self.postNotification("LayerSet.LayersChanged")
        self.dirty = True
        return layer

    # -------------
    # Dict Behavior
    # -------------

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
        self.postNotification("LayerSet.LayerWillBeDeleted", data=dict(name=name))
        layer = self._layers[name]
        self.endSelfLayerNotificationObservation(layer)
        del self._layers[name]
        self._layerOrder.remove(name)
        self._layerActionHistory.append(dict(action="delete", name=name))
        self.postNotification("LayerSet.LayerDeleted", data=dict(name=name))
        self.postNotification("LayerSet.LayersChanged")
        self.dirty = True

    def __len__(self):
        return len(self.layerOrder)

    def __contains__(self, name):
        if name is None:
            name = self._defaultLayerName
        return name in self._layers

    # ----
    # Save
    # ----

    def getSaveProgressBarTickCount(self, formatVersion):
        """
        Get the number of ticks that will be used by a progress bar
        in the save method. This method should not be called externally.
        Subclasses may override this method to implement custom saving behavior.
        """
        count = 0
        if formatVersion < 3:
            count += 1
            count += self.defaultLayer.getSaveProgressBarTickCount(formatVersion)
        else:
            for layer in self:
                count += 1
                count += layer.getSaveProgressBarTickCount(formatVersion)
        return count

    def save(self, writer, saveAs=False, progressBar=None):
        """
        Save all layers. This method should not be called externally.
        Subclasses may override this method to implement custom saving behavior.
        """
        # work through the layer action history
        if not saveAs:
            for actionData in self._layerActionHistory:
                action = actionData["action"]
                if action == "delete":
                    layerName = actionData["name"]
                    if layerName in writer.layerContents:
                        writer.deleteGlyphSet(layerName)
                elif action == "rename":
                    oldName = actionData["oldName"]
                    newName = actionData["newName"]
                    if oldName in writer.layerContents:
                        writer.renameGlyphSet(oldName, newName)
                elif action == "default":
                    newDefault = actionData["newDefault"]
                    oldDefault = actionData["oldDefault"]
                    if oldDefault not in writer.layerContents:
                        # this will be handled by the creation of the glyph set
                        continue
                    if newDefault not in writer.layerContents:
                        # this will be handled by the creation of the glyph set
                        continue
                    # both are in the file, so do the renames
                    writer.renameGlyphSet(oldDefault, defaultLayer=False)
                    writer.renameGlyphSet(newDefault, defaultLayer=False)
                elif action == "new":
                    # this will be handled by the creation of the glyph set
                    pass
        # save the layers
        if writer.formatVersion < 3:
            if progressBar is not None:
                progressBar.update(text="Saving glyphs...", increment=0)
            layer = self.defaultLayer
            glyphSet = writer.getGlyphSet(layerName=None, defaultLayer=True)
            layer.save(glyphSet, saveAs=saveAs, progressBar=progressBar)
            if progressBar is not None:
                progressBar.update()
        else:
            for layerName in self.layerOrder:
                if progressBar is not None:
                    progressBar.update(text="Saving layer \"%s\"..." % layerName, increment=0)
                layer = self[layerName]
                isDefaultLayer = layer == self.defaultLayer
                glyphSet = writer.getGlyphSet(layerName=layerName, defaultLayer=isDefaultLayer)
                layer.save(glyphSet, saveAs=saveAs, progressBar=progressBar)
                if layer.lib or layer.color:
                    glyphSet.writeLayerInfo(layer)
                self._stampLayerInfoDataState(layer)
                layer.dirty = False
                if progressBar is not None:
                    progressBar.update()
            writer.writeLayerContents(self.layerOrder)
        # reset the action history
        self._layerActionHistory = []
        # if < UFO 3 was written, flag all of the non-default layers as "new"
        defaultLayer = self.defaultLayer
        for layer in self:
            if layer == defaultLayer:
                continue
            self._layerActionHistory.append(dict(action="new", name=layer.name))

    # ------------------------
    # Notification Observation
    # ------------------------

    def endSelfNotificationObservation(self):
        if self.dispatcher is None:
            return
        for layer in list(self._layers.values()):
            self.endSelfLayerNotificationObservation(layer)
        super(LayerSet, self).endSelfNotificationObservation()
        self._font = None

    def _layerDirtyStateChange(self, notification):
        self.postNotification("LayerSet.LayerChanged")
        self.dirty = True

    def _layerNameChange(self, notification):
        data = notification.data
        oldName = data["oldName"]
        newName = data["newName"]
        self._layers[newName] = self._layers.pop(oldName)
        index = self._layerOrder.index(oldName)
        self._layerOrder.pop(index)
        self._layerOrder.insert(index, newName)
        self._layerActionHistory.append(dict(action="rename", oldName=oldName, newName=newName))

    # ---------------------
    # External Edit Support
    # ---------------------

    def _stampLayerInfoDataState(self, layer):
        if layer._glyphSet is None:
            return
        # there isn't a mod time function
        # so load the data and pack it.
        i = _StaticLayerInfoMaker()
        layer._glyphSet.readLayerInfo(i)
        layer._dataOnDisk = i.pack()

    def testForExternalChanges(self, reader):
        """
        Test for external changes. This should not be called externally.
        """
        # changed default
        defaultLayerName = self._defaultLayerName
        onDiskDefaultLayerName = reader.getDefaultLayerName()
        defaultLayerChanged = defaultLayerName != onDiskDefaultLayerName
        # changed layer order
        onDiskLayerOrder = reader.getLayerNames()
        layerOrderChanged = onDiskLayerOrder != self.layerOrder
        # layers added since we started up
        addedLayers = []
        for layerName in set(onDiskLayerOrder) - set(self.layerOrder):
            # try to filter out layers that were removed in memory
            wasDeletedInMemory = False
            for actionData in self._layerActionHistory:
                action = actionData["action"]
                if action == "delete" and actionData["name"] == layerName:
                    wasDeletedInMemory = True
            if not wasDeletedInMemory:
                addedLayers.append(layerName)
        # layers deleted since we started up
        deletedLayers = list(set(self.layerOrder) - set(onDiskLayerOrder))
        # modified layers
        modifiedLayers = {}
        for layerName in self.layerOrder:
            layer = self[layerName]
            newLayerInfo = _StaticLayerInfoMaker()
            layerInfoChanged = False
            if layer._glyphSet is not None:
                layer._glyphSet.readLayerInfo(newLayerInfo)
                layerInfoChanged = layer._dataOnDisk != newLayerInfo.pack()
            modifiedGlyphs, addedGlyphs, deletedGlyphs = layer.testForExternalChanges()
            if modifiedGlyphs or addedGlyphs or deletedGlyphs or layerInfoChanged:
                modifiedLayers[layerName] = dict(
                    info=layerInfoChanged,
                    modified=modifiedGlyphs,
                    added=addedGlyphs,
                    deleted=deletedGlyphs
                )
        # pack
        result = dict(
            defaultLayer=defaultLayerChanged,
            order=layerOrderChanged,
            added=addedLayers,
            deleted=deletedLayers,
            modified=modifiedLayers
        )
        # cross your fingers
        return result

    def reloadLayers(self, layerData):
        """
        Reload the layers. This should not be called externally.
        """
        reader = UFOReader(self.font.path)
        # handle the layers
        currentLayerOrder = self.layerOrder
        for layerName, l in list(layerData.get("layers", {}).items()):
            # new layer
            if layerName not in currentLayerOrder:
                glyphSet = reader.getGlyphSet(layerName)
                self.newLayer(layerName, glyphSet)
            # get the layer
            layer = self[layerName]
            # reload the layer info
            if l.get("info"):
                layer.color = None
                layer.lib.clear()
                layer._glyphSet.readLayerInfo(layer)
                self._stampLayerInfoDataState(layer)
            # reload the glyphs
            glyphNames = l.get("glyphNames", [])
            if glyphNames:
                layer.reloadGlyphs(glyphNames)
        # handle the order
        if layerData.get("order", False):
            newLayerOrder = reader.getLayerNames()
            for layerName in self.layerOrder:
                if layerName not in newLayerOrder:
                    newLayerOrder.append(layerName)
            self.layerOrder = newLayerOrder
        # handle the default layer
        if layerData.get("default", False):
            newDefaultLayerName = reader.getDefaultLayerName()
            self.defaultLayer = self[newDefaultLayerName]

    # -----------------------------
    # Serialization/Deserialization
    # -----------------------------

    def getDataForSerialization(self, **kwargs):
        serialize = lambda item: item.getDataForSerialization();

        def get_layers(k):
            layers = []
            for name in self.layerOrder:
                layer = self[name]
                isDefaultLayer = layer == self.defaultLayer
                layers.append((name, serialize(layer), isDefaultLayer))
            return layers

        getters = [('layers', get_layers)]

        return self._serialize(getters, **kwargs)

    def setDataFromSerialization(self, data):
        from functools import partial

        if 'layers' not in data:
            return;
        for name, data, isDefault in data['layers']:
            layer = self.newLayer(name)
            layer.setDataFromSerialization(data)
            if isDefault:
                self.defaultLayer = layer;

class _StaticLayerInfoMaker(object):

    def __init__(self):
        self.lib = {}
        self.color = None

    def pack(self):
        from ufoLib.plistlib import writePlistToString
        data = {}
        if self.lib:
            data["lib"] = self.lib
        if self.color is not None:
            data["color"] = self.color
        return writePlistToString(data)

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
    ['public.default', 'public.background', 'Layer 1']
    >>> layers.layerOrder = list(reversed(layers.layerOrder))
    >>> layers.layerOrder
    ['Layer 1', 'public.background', 'public.default']
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
    ['public.default', 'public.background', 'Layer 1', 'Test']
    """

def _testIter():
    """
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> layers = font.layers
    >>> [layer.name for layer in layers]
    ['public.default', 'public.background', 'Layer 1']
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
    >>> import os
    >>> from defcon import Font
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> font = Font(makeTestFontCopy())
    >>> path = os.path.join(font.path, "glyphs.public.background")
    >>> os.path.exists(path)
    True
    >>> layers = font.layers
    >>> del layers["public.background"]
    >>> layers.dirty = True
    >>> layers.layerOrder
    ['public.default', 'Layer 1']
    >>> "public.background" in layers
    False
    >>> len(layers)
    2
    >>> layers["public.background"]
    Traceback (most recent call last):
        ...
    KeyError: 'public.background'
    >>> font.save()
    >>> path = os.path.join(font.path, "glyphs.public.background")
    >>> os.path.exists(path)
    False
    >>> tearDownTestFontCopy()

    >>> font = Font(makeTestFontCopy())
    >>> path = os.path.join(font.path, "glyphs.public.background")
    >>> del font.layers["public.background"]
    >>> layer = font.newLayer("public.background")
    >>> layer.newGlyph("B")
    >>> font.save()
    >>> os.path.exists(os.path.join(path, "A_.glif"))
    False
    >>> os.path.exists(os.path.join(path, "B_.glif"))
    True
    >>> tearDownTestFontCopy()
    """

def _testLayerInfo():
    """
    >>> import os
    >>> from defcon import Font
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy

    # open and change some values
    >>> font = Font(makeTestFontCopy())
    >>> layer = font.layers["Layer 1"]
    >>> layer.color
    '0.1,0.2,0.3,0.4'
    >>> layer.color = '0.5,0.5,0.5,0.5'
    >>> layer.lib
    {'com.typesupply.defcon.test': '1 2 3'}
    >>> layer.lib["foo"] = "bar"
    >>> font.save()
    >>> path = font.path

    # reopen and check the changes
    >>> font = Font(path)
    >>> layer = font.layers["Layer 1"]
    >>> layer.color
    '0.5,0.5,0.5,0.5'
    >>> sorted(layer.lib.items())
    [('com.typesupply.defcon.test', '1 2 3'), ('foo', 'bar')]
    >>> tearDownTestFontCopy()
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

def _testNameChange():
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
    ['public.default', 'Name Change Test', 'Layer 1']
    >>> layer.dirty
    True
    >>> layers.dirty
    True
    """

def _testExternalChanges():
    """
    >>> import os
    >>> import shutil
    >>> from plistlib import readPlist, writePlist
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath, makeTestFontCopy, tearDownTestFontCopy

    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> font = Font(path)
    >>> reader = UFOReader(path)
    >>> font.layers.testForExternalChanges(reader)
    {'deleted': [], 'added': [], 'modified': {}, 'defaultLayer': False, 'order': False}
    >>> tearDownTestFontCopy(font.path)

    # layerinfo.plist
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> font = Font(path)
    >>> reader = UFOReader(path)
    >>> p = os.path.join(path, "glyphs", "layerinfo.plist")
    >>> data = {"lib" : {}}
    >>> data["lib"]["testForExternalChanges.test"] = 1
    >>> writePlist(data, p)
    >>> font.layers.testForExternalChanges(reader)["modified"]["public.default"]["info"]
    True
    >>> tearDownTestFontCopy(font.path)

    # add a layer
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> font = Font(path)
    >>> shutil.copytree(os.path.join(path, "glyphs"), os.path.join(path, "glyphs.test"))
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> contents.append(("test", "glyphs.test"))
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> reader = UFOReader(path)
    >>> font.layers.testForExternalChanges(reader)["added"]
    ['test']
    >>> tearDownTestFontCopy(font.path)

    # remove a layer
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> shutil.copytree(os.path.join(path, "glyphs"), os.path.join(path, "glyphs.test"))
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> contents.append(("test", "glyphs.test"))
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font = Font(path)
    >>> shutil.rmtree(os.path.join(path, "glyphs.test"))
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> n = contents.pop(1)
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> reader = UFOReader(path)
    >>> font.layers.testForExternalChanges(reader)["deleted"]
    ['test']
    >>> tearDownTestFontCopy(font.path)

    # change the layer order
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> shutil.copytree(os.path.join(path, "glyphs"), os.path.join(path, "glyphs.test"))
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> contents.append(("test", "glyphs.test"))
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font = Font(path)
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> contents.reverse()
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> reader = UFOReader(path)
    >>> font.layers.testForExternalChanges(reader)
    {'deleted': [], 'added': [], 'modified': {}, 'defaultLayer': False, 'order': True}
    >>> tearDownTestFontCopy(font.path)

    # change the default layer
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> shutil.copytree(os.path.join(path, "glyphs"), os.path.join(path, "glyphs.test"))
    >>> contents = [("foo", "glyphs"), ("test", "glyphs.test")]
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font = Font(path)
    >>> contents = [("test", "glyphs"), ("foo", "glyphs.test")]
    >>> contents.reverse()
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> reader = UFOReader(path)
    >>> font.layers.testForExternalChanges(reader)
    {'deleted': [], 'added': [], 'modified': {}, 'defaultLayer': True, 'order': False}
    >>> tearDownTestFontCopy(font.path)
    """

def _testReloadLayers():
    """
    >>> import os
    >>> import shutil
    >>> from plistlib import readPlist, writePlist
    >>> from defcon import Font
    >>> from defcon.test.testTools import getTestFontPath, makeTestFontCopy, tearDownTestFontCopy

    # layerinfo.plist
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> font = Font(path)
    >>> p = os.path.join(path, "glyphs", "layerinfo.plist")
    >>> data = {"lib" : {}}
    >>> data["lib"]["testForExternalChanges.test"] = 1
    >>> writePlist(data, p)
    >>> font.reloadLayers(dict(layers={"public.default" : dict(info=True)}))
    >>> font.layers["public.default"].lib
    {'testForExternalChanges.test': 1}
    >>> tearDownTestFontCopy(font.path)

    # add a layer
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> font = Font(path)
    >>> shutil.copytree(os.path.join(path, "glyphs"), os.path.join(path, "glyphs.test"))
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> contents.append(("test", "glyphs.test"))
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font.reloadLayers(dict(layers={"test" : {}}))
    >>> font.layers.layerOrder
    ['public.default', 'test']
    >>> tearDownTestFontCopy(font.path)

    # change the layer order
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> shutil.copytree(os.path.join(path, "glyphs"), os.path.join(path, "glyphs.test"))
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> contents.append(("test", "glyphs.test"))
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font = Font(path)
    >>> contents = readPlist(os.path.join(path, "layercontents.plist"))
    >>> contents.reverse()
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font.reloadLayers(dict(order=True))
    >>> font.layers.layerOrder
    ['test', 'public.default']
    >>> tearDownTestFontCopy(font.path)

    # change the default layer
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> path = makeTestFontCopy(path)
    >>> shutil.copytree(os.path.join(path, "glyphs"), os.path.join(path, "glyphs.test"))
    >>> contents = [("foo", "glyphs"), ("test", "glyphs.test")]
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font = Font(path)
    >>> contents = [("test", "glyphs"), ("foo", "glyphs.test")]
    >>> contents.reverse()
    >>> writePlist(contents, os.path.join(path, "layercontents.plist"))
    >>> font.reloadLayers(dict(default=True))
    >>> font.layers.defaultLayer.name
    'test'
    >>> tearDownTestFontCopy(font.path)
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
