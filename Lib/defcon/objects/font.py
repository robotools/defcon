import os
import re
import weakref
from copy import deepcopy
import tempfile
import shutil
from fontTools.misc.arrayTools import unionRect
import ufoLib
from defcon.errors import DefconError
from defcon.objects.base import BaseObject
from defcon.objects.layerSet import LayerSet
from defcon.objects.layer import Layer
from defcon.objects.info import Info
from defcon.objects.kerning import Kerning
from defcon.objects.groups import Groups
from defcon.objects.features import Features
from defcon.objects.lib import Lib
from defcon.objects.images import Images
from defcon.tools.notifications import NotificationCenter


class Font(BaseObject):

    """
    If loading from an existing UFO, **path** should be the path to the UFO.

    If you subclass one of the sub objects, such as :class:`Glyph`,
    the class must be registered when the font is created for defcon
    to know about it. The **\*Class** arguments allow for individual
    ovverrides. If None is provided for an argument, the defcon
    appropriate class will be used.

    **This object posts the following notifications:**

    ===================  ====
    Name                 Note
    ===================  ====
    Font.Changed         Posted when the *dirty* attribute is set.
    Font.ReloadedGlyphs  Posted after the *reloadGlyphs* method has been called.
    ===================  ====

    The Font object has some dict like behavior. For example, to get a glyph::

        glyph = font["aGlyphName"]

    To iterate over all glyphs::

        for glyph in font:

    To get the number of glyphs::

        glyphCount = len(font)

    To find out if a font contains a particular glyph::

        exists = "aGlyphName" in font

    To remove a glyph::

        del font["aGlyphName"]
    """

    changeNotificationName = "Font.Changed"

    def __init__(self, path=None,
                    kerningClass=None, infoClass=None, groupsClass=None, featuresClass=None, libClass=None, unicodeDataClass=None,
                    layerSetClass=None, layerClass=None, imagesClass=None,
                    glyphClass=None, glyphContourClass=None, glyphPointClass=None, glyphComponentClass=None, glyphAnchorClass=None):
        super(Font, self).__init__()
        if infoClass is None:
            infoClass = Info
        if kerningClass is None:
            kerningClass = Kerning
        if groupsClass is None:
            groupsClass = Groups
        if featuresClass is None:
            featuresClass = Features
        if libClass is None:
            libClass = Lib
        if layerSetClass is None:
            layerSetClass = LayerSet
        if imagesClass is None:
            imagesClass = Images

        self._dispatcher = NotificationCenter()

        self._kerningClass = kerningClass
        self._infoClass = infoClass
        self._groupsClass = groupsClass
        self._featuresClass = featuresClass
        self._libClass = libClass

        self._path = path
        self._ufoFormatVersion = None

        self._kerning = None
        self._info = None
        self._groups = None
        self._features = None
        self._lib = None

        self._layers = layerSetClass(
            libClass=libClass, unicodeDataClass=unicodeDataClass,
            layerClass=layerClass, glyphClass=glyphClass,
            glyphContourClass=glyphContourClass, glyphPointClass=glyphPointClass,
            glyphComponentClass=glyphComponentClass, glyphAnchorClass=glyphAnchorClass
        )
        self._layers.dispatcher = self.dispatcher
        self._layers.setParent(self)
        self._layers.addObserver(self, "_objectDirtyStateChange", "LayerSet.Changed")

        self._images = Images()
        self._images.setParent(self)
        self._images._dispatcher = self._dispatcher

        self._dirty = False

        if path:
            reader = ufoLib.UFOReader(self._path)
            self._ufoFormatVersion = reader.formatVersion
            # go ahead and load the layers
            layerNames = reader.getLayerNames()
            for layerName in layerNames:
                glyphSet = reader.getGlyphSet(layerName)
                layer = self._layers.newLayer(layerName, glyphSet=glyphSet)
                glyphSet.readLayerInfo(layer)
                layer._dirty = False
            defaultLayerName = reader.getDefaultLayerName()
            self._layers.defaultLayer = self._layers[defaultLayerName]
            self._layers.dirty = False
            # get the image file names
            self._images.fileNames = reader.getImageDirectoryListing()
            # if the UFO version is 1, do some conversion.
            if self._ufoFormatVersion == 1:
                self._convertFromFormatVersion1RoboFabData()
            # if the ufo version is < 3, read the kerning and groups
            # right now. do this by creating a reference to the reader.
            # otherwsie a situation could arise where the groups
            # are modified by an external source before being read.
            # that could create a data corruption within this object.
            if self._ufoFormatVersion < 3:
                self._reader = reader
                k = self.kerning
                g = self.groups

        if self._layers.defaultLayer is None:
            layer = self.newLayer("public.default")
            self._layers.defaultLayer = layer

    # ------
    # Glyphs
    # ------

    def _get_glyphSet(self):
        return self._layers.defaultLayer

    _glyphSet = property(_get_glyphSet, doc="Convenience for getting the main layer.")

    def newGlyph(self, name):
        """
        Create a new glyph with **name** in the font's main layer.
        If a glyph with that name already exists, the existing
        glyph will be replaced with the new glyph.
        """
        return self._glyphSet.newGlyph(name)

    def insertGlyph(self, glyph, name=None):
        """
        Insert **glyph** into the font's main layer.
        Optionally, the glyph can be renamed at the same time by
        providing **name**. If a glyph with the glyph name, or
        the name provided as **name**, already exists, the existing
        glyph will be replaced with the new glyph.
        """
        return self._glyphSet.insertGlyph(glyph, name=name)

    def __iter__(self):
        names = self._glyphSet.keys()
        while names:
            name = names[0]
            yield self._glyphSet[name]
            names = names[1:]

    def __getitem__(self, name):
        return self._glyphSet[name]

    def __delitem__(self, name):
        del self._glyphSet[name]

    def __len__(self):
        return len(self._glyphSet)

    def __contains__(self, name):
        return name in self._glyphSet

    def keys(self):
        return self._glyphSet.keys()

    # ------
    # Layers
    # ------

    def newLayer(self, name):
        return self._layers.newLayer(name)

    # ----------
    # Attributes
    # ----------

    def _get_path(self):
        return self._path

    def _set_path(self, path):
        # XXX: this needs to be reworked for layers
        # the file must already exist
        assert os.path.exists(path)
        # the glyphs directory must already exist
        glyphsDir = os.path.join(path, "glyphs")
        assert os.path.exists(glyphsDir)
        # set the internal reference
        self._path = path
        # set the glyph set reference
        if self._glyphSet is not None:
            self._glyphSet.dirName = glyphsDir

    path = property(_get_path, _set_path, doc="The location of the file on disk. Setting the path should only be done when the user has moved the file in the OS interface. Setting the path is not the same as a save operation.")

    def _get_ufoFormatVersion(self):
        return self._ufoFormatVersion

    ufoFormatVersion = property(_get_ufoFormatVersion, doc="The UFO format version that will be used when saving. This is taken from a loaded UFO during __init__. If this font was not loaded from a UFO, this will return None until the font has been saved.")

    def _get_glyphsWithOutlines(self):
        return self._glyphSet.glyphsWithOutlines

    glyphsWithOutlines = property(_get_glyphsWithOutlines, doc="A list of glyphs containing outlines in the font's main layer.")

    def _get_componentReferences(self):
        return self._glyphSet.componentReferences

    componentReferences = property(_get_componentReferences, doc="A dict of describing the component relationships in the font's main layer. The dictionary is of form ``{base glyph : [references]}``.")

    def _get_bounds(self):
        return self._glyphSet.bounds

    bounds = property(_get_bounds, doc="The bounds of all glyphs in the font's main layer. This can be an expensive operation.")

    def _get_controlPointBounds(self):
        return self._glyphSet.controlPointBounds

    controlPointBounds = property(_get_controlPointBounds, doc="The control bounds of all glyphs in the font's main layer. This only measures the point positions, it does not measure curves. So, curves without points at the extrema will not be properly measured. This is an expensive operation.")

    # -----------
    # Sub-Objects
    # -----------

    def _get_layers(self):
        return self._layers

    layers = property(_get_layers, doc="The font's :class:`LayerSet` object.")

    def _get_info(self):
        if self._info is None:
            self._info = self._infoClass()
            self._info.dispatcher = self.dispatcher
            self._info.setParent(self)
            if self._path is not None:
                reader = ufoLib.UFOReader(self._path)
                reader.readInfo(self._info)
                self._info.dirty = False
            self._info.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Info.Changed")
            self._stampInfoDataState()
        return self._info

    info = property(_get_info, doc="The font's :class:`Info` object.")

    def _get_kerning(self):
        if self._kerning is None:
            self._kerning = self._kerningClass()
            self._kerning.dispatcher = self.dispatcher
            self._kerning.setParent(self)
            if self._path is not None:
                # the _reader attribute may be present during __init__
                # but only under certain conditions.
                if hasattr(self, "_reader"):
                    reader = self._reader
                else:
                    reader = ufoLib.UFOReader(self._path)
                d = reader.readKerning()
                self._kerning.update(d)
                self._kerning.dirty = False
            self._kerning.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Kerning.Changed")
            self._stampKerningDataState()
        return self._kerning

    kerning = property(_get_kerning, doc="The font's :class:`Kerning` object.")

    def _get_groups(self):
        if self._groups is None:
            self._groups = self._groupsClass()
            self._groups.dispatcher = self.dispatcher
            self._groups.setParent(self)
            if self._path is not None:
                # the _reader attribute may be present during __init__
                # but only under certain conditions.
                if hasattr(self, "_reader"):
                    reader = self._reader
                else:
                    reader = ufoLib.UFOReader(self._path)
                d = reader.readGroups()
                self._groups.update(d)
                self._groups.dirty = False
            self._groups.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Groups.Changed")
            self._stampGroupsDataState()
        return self._groups

    groups = property(_get_groups, doc="The font's :class:`Groups` object.")

    def _get_features(self):
        if self._features is None:
            self._features = self._featuresClass()
            self._features.dispatcher = self.dispatcher
            self._features.setParent(self)
            if self._path is not None:
                reader = ufoLib.UFOReader(self._path)
                t = reader.readFeatures()
                self._features.text = t
                self._features.dirty = False
            self._features.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Features.Changed")
            self._stampFeaturesDataState()
        return self._features

    features = property(_get_features, doc="The font's :class:`Features` object.")

    def _get_lib(self):
        if self._lib is None:
            self._lib = self._libClass()
            self._lib.dispatcher = self.dispatcher
            self._lib.setParent(self)
            if self._path is not None:
                reader = ufoLib.UFOReader(self._path)
                d = reader.readLib()
                self._lib.update(d)
            self._lib.addObserver(observer=self, methodName="_objectDirtyStateChange", notification="Lib.Changed")
            self._stampLibDataState()
        return self._lib

    lib = property(_get_lib, doc="The font's :class:`Lib` object.")

    def _get_unicodeData(self):
        return self._glyphSet._unicodeData

    unicodeData = property(_get_unicodeData, doc="The font's :class:`UnicodeData` object.")

    def _get_images(self):
        return self._images

    images = property(_get_images, doc="The font's :class:`Images` object.")

    # -------
    # Methods
    # -------

    def save(self, path=None, formatVersion=None, progressBar=None):
        """
        Save the font to **path**. If path is None, the path
        from the last save or when the font was first opened
        will be used.

        The UFO will be saved using the format found at ``ufoFormatVersion``.
        This value is either the format version from the exising UFO or
        the format version specified in a previous save. If neither of
        these is available, the UFO will be written as format version 2.
        If you wish to specifiy the format version for saving, pass
        the desired number as the **formatVersion** argument.
        """
        saveAs = False
        if path is not None and path != self._path:
            saveAs = True
        else:
            path = self._path
        ## work out the format version
        # if None is given, fallback to the one that
        # came in when the UFO was loaded
        if formatVersion is None and self._ufoFormatVersion is not None:
            formatVersion = self._ufoFormatVersion
        # otherwise fallback to 3
        elif self._ufoFormatVersion is None:
            formatVersion = 3
        # if down-converting, use a temp directory
        downConvertinginPlace = False
        if path == self._path and formatVersion < self._ufoFormatVersion:
            downConvertinginPlace = True
            path = os.path.join(tempfile.mkdtemp(), "temp.ufo")
        try:
            # make a UFOWriter
            writer = ufoLib.UFOWriter(path, formatVersion=formatVersion)
            # if changing ufo format versions, flag all objects
            # as dirty so that they will be saved
            if self._ufoFormatVersion != formatVersion:
                self.info.dirty = True
                self.groups.dirty = True
                self.kerning.dirty = True
                self.lib.dirty = True
                if formatVersion > 1:
                    self.features.dirty = True
            # save the objects
            self.saveInfo(writer=writer, saveAs=saveAs, progressBar=progressBar)
            self.saveGroups(writer=writer, saveAs=saveAs, progressBar=progressBar)
            self.saveKerning(writer=writer, saveAs=saveAs, progressBar=progressBar)
            self.saveLib(writer=writer, saveAs=saveAs, progressBar=progressBar)
            if formatVersion >= 2:
                self.saveFeatures(writer=writer, saveAs=saveAs, progressBar=progressBar)
            if formatVersion >= 3:
                self.saveImages(writer=writer, saveAs=saveAs, progressBar=progressBar)
                self.saveData(writer=writer, saveAs=saveAs, progressBar=progressBar)
            self.layers.save(writer, saveAs=saveAs, progressBar=progressBar)
            if downConvertinginPlace:
                shutil.rmtree(self._path)
                shutil.move(path, self._path)
                # XXX reset internal time stamping on things that weren't saved
        finally:
            # if down converting in place, handle the temp
            if downConvertinginPlace:
                shutil.rmtree(os.path.dirname(path))
                path = self._path
        # done
        self._path = path
        self._ufoFormatVersion = formatVersion
        self.dirty = False

    def saveInfo(self, writer, saveAs=False, progressBar=None):
        # info should always be saved
        if progressBar is not None:
            progressBar.setTitle("Saving info...")
        writer.writeInfo(self.info)
        self.info.dirty = False
        self._stampInfoDataState()
        if progressBar is not None:
            progressBar.tick()

    def saveGroups(self, writer, saveAs=False, progressBar=None):
        # groups should always be saved
        if progressBar is not None:
            progressBar.setTitle("Saving groups...")
        writer.writeGroups(self.groups)
        self.groups.dirty = False
        self._stampGroupsDataState()
        if progressBar is not None:
            progressBar.tick()

    def saveKerning(self, writer, saveAs=False, progressBar=None):
        if progressBar is not None:
            progressBar.setTitle("Saving kerning...")
        if self.kerning.dirty or saveAs:
            writer.writeKerning(self.kerning)
            self.kerning.dirty = False
            self._stampKerningDataState()
        if progressBar is not None:
            progressBar.tick()

    def saveFeatures(self, writer, saveAs=False, progressBar=None):
        if progressBar is not None:
            progressBar.setTitle("Saving features...")
        if self.features.dirty or saveAs:
            writer.writeFeatures(self.features.text)
            self.features.dirty = False
            self._stampFeaturesDataState()
        if progressBar is not None:
            progressBar.tick()

    def saveLib(self, writer, saveAs=False, progressBar=None):
        # lib should always be saved
        if progressBar is not None:
            progressBar.setTitle("Saving lib...")
        # if making format version 1, do some
        # temporary down conversion before
        # passing the lib to the writer
        libCopy = dict(self.lib)
        if writer.formatVersion == 1:
            self._convertToFormatVersion1RoboFabData(libCopy)
        writer.writeLib(libCopy)
        self.lib.dirty = False
        self._stampLibDataState()
        if progressBar is not None:
            progressBar.tick()

    def saveImages(self, writer, saveAs=False, progressBar=None):
        if progressBar is not None:
            progressBar.setTitle("Saving images...")
        self.images.save(writer, saveAs=saveAs, progressBar=progressBar)
        if progressBar is not None:
            progressBar.tick()

    def saveData(self, writer, saveAs=False, progressBar=None):
        pass

    # ----------------------
    # Notification Callbacks
    # ----------------------

    def _objectDirtyStateChange(self, notification):
        if notification.object.dirty:
            self.dirty = True

    # ---------------------
    # External Edit Support
    # ---------------------

    # data stamping

    def _stampFontDataState(self, obj, fileName):
        # font is not on disk
        if self._path is None:
            return
        # data has not been loaded
        if obj is None:
            return
        path = os.path.join(self._path, fileName)
        # file is not in UFO
        if not os.path.exists(path):
            text = None
            modTime = -1
        # get the text
        else:
            f = open(path, "rb")
            text = f.read()
            f.close()
            # get the file modification time
            modTime = os.stat(path).st_mtime
        # store the data
        obj._dataOnDisk = text
        obj._dataOnDiskTimeStamp = modTime

    def _stampInfoDataState(self):
        self._stampFontDataState(self._info, "fontinfo.plist")

    def _stampKerningDataState(self):
        self._stampFontDataState(self._kerning, "kerning.plist")

    def _stampGroupsDataState(self):
        self._stampFontDataState(self._groups, "groups.plist")

    def _stampFeaturesDataState(self):
        self._stampFontDataState(self._features, "features.fea")

    def _stampLibDataState(self):
        self._stampFontDataState(self._lib, "lib.plist")

    def _stampGlyphDataState(self, glyph):
        if self._glyphSet is None:
            return
        glyphSet = self._glyphSet
        glyphName = glyph.name
        if glyphName not in glyphSet.contents:
            return
        path = os.path.join(self.path, "glyphs", glyphSet.contents[glyphName])
        # get the text
        f = open(path, "rb")
        text = f.read()
        f.close()
        # get the file modification time
        modTime = os.stat(path).st_mtime
        # store the data
        glyph._dataOnDisk = text
        glyph._dataOnDiskTimeStamp = modTime

    # data comparison

    def testForExternalChanges(self):
        """
        Test the UFO for changes that occured outside of this font's
        tree of objects. This returns a dictionary of values
        indicating if the objects have changes on disk that are
        not loaded. For example::

            {
                "info" : False,
                "kerning" : True,
                "groups" : True,
                "features" : False,
                "lib" : False,
                "modifiedGlyphs" : ["a", "a.alt"],
                "addedGlyphs" : [],
                "deletedGlyphs" : []
            }

        It is important to keep in mind that the user could have created
        conflicting data outside of the font's tree of objects. For example,
        say the user has set ``font.info.unitsPerEm = 1000`` inside of the
        font's :class:`Info` object and the user has not saved this change.
        In the the font's fontinfo.plist file, the user sets the unitsPerEm value
        to 2000. Which value is current? Which value is right? defcon leaves
        this decision up to you.
        """
        infoChanged = self._testInfoForExternalModifications()
        kerningChanged = self._testKerningForExternalModifications()
        groupsChanged = self._testGroupsForExternalModifications()
        featuresChanged = self._testFeaturesForExternalModifications()
        libChanged = self._testLibForExternalModifications()
        modifiedGlyphs, addedGlyphs, deletedGlyphs = self._testGlyphsForExternalModifications()
        return dict(
            info=infoChanged,
            kerning=kerningChanged,
            groups=groupsChanged,
            features=featuresChanged,
            lib=libChanged,
            modifiedGlyphs=modifiedGlyphs,
            addedGlyphs=addedGlyphs,
            deletedGlyphs=deletedGlyphs
        )

    def _testFontDataForExternalModifications(self, obj, fileName):
        # font is not on disk
        if self._path is None:
            return False
        # data has not been loaded
        if obj is None:
            return False
        path = os.path.join(self._path, fileName)
        # file is not in UFO
        if not os.path.exists(path):
            # if there was data in the file before
            if obj._dataOnDisk:
                return True
            return False
        # mod time mismatch
        modTime = os.stat(path).st_mtime
        if obj._dataOnDiskTimeStamp != modTime:
            f = open(path, "rb")
            text = f.read()
            f.close()
            # text mismatch
            if text != obj._dataOnDisk:
                return True
        return False

    def _testInfoForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._info, "fontinfo.plist")

    def _testKerningForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._kerning, "kerning.plist")

    def _testGroupsForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._groups, "groups.plist")

    def _testFeaturesForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._features, "features.fea")

    def _testLibForExternalModifications(self):
        return self._testFontDataForExternalModifications(self._lib, "lib.plist")

    def _testGlyphsForExternalModifications(self):
        # font is not stored on disk
        if self._glyphSet is None:
            return [], [], []
        glyphSet = self._glyphSet
        glyphSet.rebuildContents()
        # glyphs added since we started up
        addedGlyphs = list(set(self._glyphSet.keys()) - self._keys)
        # glyphs deleted since we started up
        deletedGlyphs = list(self._keys - set(self._glyphSet.keys()))
        # glyphs modified since loading
        modifiedGlyphs = []
        for glyphName, glyph in self._glyphs.items():
            # deleted glyph. skip.
            if glyphName not in glyphSet.contents:
                continue
            path = os.path.join(self.path, "glyphs", glyphSet.contents[glyphName])
            modTime = os.stat(path).st_mtime
            # mod time mismatch
            if modTime != glyph._dataOnDiskTimeStamp:
                f = open(path, "rb")
                text = f.read()
                f.close()
                # data mismatch
                if text != glyph._dataOnDisk:
                    modifiedGlyphs.append(glyphName)
        # add loaded glyphs to the keys
        self._keys = self._keys | set(addedGlyphs)
        return modifiedGlyphs, addedGlyphs, deletedGlyphs

    # data reloading

    def reloadInfo(self):
        """
        Reload the data in the :class:`Info` object from the
        fontinfo.plist file in the UFO.
        """
        if self._info is None:
            obj = self.info
        else:
            r = ufoLib.UFOReader(self._path)
            newInfo = Info()
            r.readInfo(newInfo)
            oldInfo = self._info
            for attr in dir(newInfo):
                if attr in ufoLib.deprecatedFontInfoAttributesVersion2:
                    continue
                if attr.startswith("_"):
                    continue
                if attr == "dirty":
                    continue
                if attr == "dispatcher":
                    continue
                if not hasattr(oldInfo, attr):
                    continue
                newValue = getattr(newInfo, attr)
                oldValue = getattr(oldInfo, attr)
                if hasattr(newValue, "im_func"):
                    continue
                if oldValue == newValue:
                    continue
                setattr(oldInfo, attr, newValue)
            self._stampInfoDataState()

    def reloadKerning(self):
        """
        Reload the data in the :class:`Kerning` object from the
        kerning.plist file in the UFO.
        """
        if self._kerning is None:
            obj = self.kerning
        else:
            r = ufoLib.UFOReader(self._path)
            d = r.readKerning()
            self._kerning.clear()
            self._kerning.update(d)
            self._stampKerningDataState()

    def reloadGroups(self):
        """
        Reload the data in the :class:`Groups` object from the
        groups.plist file in the UFO.
        """
        if self._groups is None:
            obj = self.groups
        else:
            r = ufoLib.UFOReader(self._path)
            d = r.readGroups()
            self._groups.clear()
            self._groups.update(d)
            self._stampGroupsDataState()

    def reloadFeatures(self):
        """
        Reload the data in the :class:`Features` object from the
        features.fea file in the UFO.
        """
        if self._features is None:
            obj = self.features
        else:
            r = ufoLib.UFOReader(self._path)
            text = r.readFeatures()
            self._features.text = text
            self._stampFeaturesDataState()

    def reloadLib(self):
        """
        Reload the data in the :class:`Lib` object from the
        lib.plist file in the UFO.
        """
        if self._lib is None:
            obj = self.lib
        else:
            r = ufoLib.UFOReader(self._path)
            d = r.readLib()
            self._lib.clear()
            self._lib.update(d)
            self._stampLibDataState()

    def reloadGlyphs(self, glyphNames):
        """
        Reload the glyphs listed in **glyphNames** from the
        appropriate files within the UFO. When all of the
        loading is complete, a *Font.ReloadedGlyphs* notification
        will be posted.
        """
        for glyphName in glyphNames:
            if glyphName not in self._glyphs:
                self._loadGlyph(glyphName)
            else:
                glyph = self._glyphs[glyphName]
                glyph.destroyAllRepresentations(None)
                glyph.clear()
                pointPen = glyph.getPointPen()
                self._glyphSet.readGlyph(glyphName=glyphName, glyphObject=glyph, pointPen=pointPen)
                glyph.dirty = False
                self._stampGlyphDataState(glyph)
        data = dict(glyphNames=glyphNames)
        self.postNotification(notification="Font.ReloadedGlyphs", data=data)
        # post a change notification for any glyphs that
        # reference the reloaded glyphs via components.
        componentReferences = self.componentReferences
        referenceChanges = set()
        for glyphName in glyphNames:
            if glyphName not in componentReferences:
                continue
            for reference in componentReferences[glyphName]:
                if reference in glyphNames:
                    continue
                if reference not in self._glyphs:
                    continue
                if reference in referenceChanges:
                    continue
                glyph = self._glyphs[reference]
                glyph.destroyAllRepresentations(None)
                glyph.postNotification(notification=glyph.changeNotificationName)
                referenceChanges.add(reference)

    # -----------------------------
    # UFO Format Version Conversion
    # -----------------------------

    def _convertFromFormatVersion1RoboFabData(self):
        # migrate features from the lib
        features = []
        classes = self.lib.get("org.robofab.opentype.classes")
        if classes is not None:
            del self.lib["org.robofab.opentype.classes"]
            features.append(classes)
        splitFeatures = self.lib.get("org.robofab.opentype.features")
        if splitFeatures is not None:
            order = self.lib.get("org.robofab.opentype.featureorder")
            if order is None:
                order = splitFeatures.keys()
                order.sort()
            else:
                del self.lib["org.robofab.opentype.featureorder"]
            del self.lib["org.robofab.opentype.features"]
            for tag in order:
                oneFeature = splitFeatures.get(tag)
                if oneFeature is not None:
                    features.append(oneFeature)
        self.features.text = "\n".join(features)
        # migrate hint data from the lib
        hintData = self.lib.get("org.robofab.postScriptHintData")
        if hintData is not None:
            del self.lib["org.robofab.postScriptHintData"]
            # settings
            blueFuzz = hintData.get("blueFuzz")
            if blueFuzz is not None:
                self.info.postscriptBlueFuzz = blueFuzz
            blueScale = hintData.get("blueScale")
            if blueScale is not None:
                self.info.postscriptBlueScale = blueScale
            blueShift = hintData.get("blueShift")
            if blueShift is not None:
                self.info.postscriptBlueShift = blueShift
            forceBold = hintData.get("forceBold")
            if forceBold is not None:
                self.info.postscriptForceBold = forceBold
            # stems
            vStems = hintData.get("vStems")
            if vStems is not None:
                self.info.postscriptStemSnapV = vStems
            hStems = hintData.get("hStems")
            if hStems is not None:
                self.info.postscriptStemSnapH = hStems
            # blues
            bluePairs = [
                ("postscriptBlueValues", "blueValues"),
                ("postscriptOtherBlues", "otherBlues"),
                ("postscriptFamilyBlues", "familyBlues"),
                ("postscriptFamilyOtherBlues", "familyOtherBlues"),
            ]
            for infoAttr, libKey in bluePairs:
                libValue = hintData.get(libKey)
                if libValue is not None:
                    value = []
                    for i, j in libValue:
                        value.append(i)
                        value.append(j)
                    setattr(self.info, infoAttr, value)

    def _convertToFormatVersion1RoboFabData(self, libCopy):
        from robofab.tools.fontlabFeatureSplitter import splitFeaturesForFontLab
        # features
        features = self.features.text
        classes, features = splitFeaturesForFontLab(features)
        if classes:
            libCopy["org.robofab.opentype.classes"] = classes.strip() + "\n"
        if features:
            featureDict = {}
            for featureName, featureText in features:
                featureDict[featureName] = featureText.strip() + "\n"
            libCopy["org.robofab.opentype.features"] = featureDict
            libCopy["org.robofab.opentype.featureorder"] = [featureName for featureName, featureText in features]
        # hint data
        hintData = dict(
            blueFuzz=self.info.postscriptBlueFuzz,
            blueScale=self.info.postscriptBlueScale,
            blueShift=self.info.postscriptBlueShift,
            forceBold=self.info.postscriptForceBold,
            vStems=self.info.postscriptStemSnapV,
            hStems=self.info.postscriptStemSnapH
        )
        bluePairs = [
            ("postscriptBlueValues", "blueValues"),
            ("postscriptOtherBlues", "otherBlues"),
            ("postscriptFamilyBlues", "familyBlues"),
            ("postscriptFamilyOtherBlues", "familyOtherBlues"),
        ]
        for infoAttr, libKey in bluePairs:
            values = getattr(self.info, infoAttr)
            if values is not None:
                finalValues = []
                for value in values:
                    if not finalValues or len(finalValues[-1]) == 2:
                        finalValues.append([])
                    finalValues[-1].append(value)
                hintData[libKey] = finalValues
        for key, value in hintData.items():
            if value is None:
                del hintData[key]
        libCopy["org.robofab.postScriptHintData"] = hintData


# -----
# Tests
# -----

def _testSetParentDataInGlyph():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> id(glyph.getParent()) == id(font)
    True
    """

def _testNewGlyph():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> font.newGlyph('NewGlyphTest')
    >>> glyph = font['NewGlyphTest']
    >>> glyph.name
    'NewGlyphTest'
    >>> glyph.dirty
    True
    >>> font.dirty
    True
    >>> keys = font.keys()
    >>> keys.sort()
    >>> keys
    ['A', 'B', 'C', 'NewGlyphTest']
    """

def _testInsertGlyph():
    """
    >>> "need insert glyph test!"
    """

def _testIter():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> names = [glyph.name for glyph in font]
    >>> names.sort()
    >>> names
    ['A', 'B', 'C']
    >>> names = []
    >>> for glyph1 in font:
    ...     for glyph2 in font:
    ...         names.append((glyph1.name, glyph2.name))
    >>> names.sort()
    >>> names
    [('A', 'A'), ('A', 'B'), ('A', 'C'), ('B', 'A'), ('B', 'B'), ('B', 'C'), ('C', 'A'), ('C', 'B'), ('C', 'C')]
    """

def _testGetitem():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> font['A'].name
    'A'
    >>> font['B'].name
    'B'
    >>> font['NotInFont']
    Traceback (most recent call last):
        ...
    KeyError: 'NotInFont not in font'
    """

def _testDelitem():
    """
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy
    >>> import glob
    >>> import os
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> del font['A']
    >>> font.dirty
    True
    >>> font.newGlyph('NewGlyphTest')
    >>> del font['NewGlyphTest']
    >>> keys = font.keys()
    >>> keys.sort()
    >>> keys
    ['B', 'C']
    >>> len(font)
    2
    >>> 'A' in font
    False
    >>> font.save()
    >>> fileNames = glob.glob(os.path.join(path, 'Glyphs', '*.glif'))
    >>> fileNames = [os.path.basename(fileName) for fileName in fileNames]
    >>> fileNames.sort()
    >>> fileNames
    ['B_.glif', 'C_.glif']
    >>> del font['NotInFont']
    Traceback (most recent call last):
        ...
    KeyError: 'NotInFont not in font'
    >>> tearDownTestFontCopy()

    # test saving externally deleted glyphs.
    # del glyph. not dirty.
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> glyph = font["A"]
    >>> glyphPath = os.path.join(path, "glyphs", "A_.glif")
    >>> os.remove(glyphPath)
    >>> r = font.testForExternalChanges()
    >>> r["deletedGlyphs"]
    ['A']
    >>> del font["A"]
    >>> font.save()
    >>> os.path.exists(glyphPath)
    False
    >>> tearDownTestFontCopy()

    # del glyph. dirty.
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> glyph = font["A"]
    >>> glyph.dirty = True
    >>> glyphPath = os.path.join(path, "glyphs", "A_.glif")
    >>> os.remove(glyphPath)
    >>> r = font.testForExternalChanges()
    >>> r["deletedGlyphs"]
    ['A']
    >>> del font["A"]
    >>> font.save()
    >>> os.path.exists(glyphPath)
    False
    >>> tearDownTestFontCopy()
    """

def _testLen():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> len(font)
    3
    
    >>> font = Font()
    >>> len(font)
    0
    """

def _testContains():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> 'A' in font
    True
    >>> 'NotInFont' in font
    False
    
    >>> font = Font()
    >>> 'A' in font
    False
    """

def _testKeys():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> keys = font.keys()
    >>> keys.sort()
    >>> print keys
    ['A', 'B', 'C']
    >>> del font["A"]
    >>> keys = font.keys()
    >>> keys.sort()
    >>> print keys
    ['B', 'C']
    >>> font.newGlyph("A")
    >>> keys = font.keys()
    >>> keys.sort()
    >>> print keys
    ['A', 'B', 'C']

    >>> font = Font()
    >>> font.keys()
    []
    >>> font.newGlyph("A")
    >>> keys = font.keys()
    >>> keys.sort()
    >>> print keys
    ['A']
    """

def _testPath():
    """
    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> font.path == path
    True

    >>> font = Font()
    >>> font.path == None
    True

    # set
    >>> import shutil
    >>> from defcon.test.testTools import getTestFontPath
    >>> path1 = getTestFontPath()
    >>> font = Font(path1)
    >>> path2 = getTestFontPath("setPathTest.ufo")
    >>> shutil.copytree(path1, path2)
    >>> font.path = path2
    >>> shutil.rmtree(path2)
    """

def _testGlyphWithOutlines():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> sorted(font.glyphsWithOutlines)
    ['A', 'B']
    >>> font = Font(getTestFontPath())
    >>> for glyph in font:
    ...    pass
    >>> sorted(font.glyphsWithOutlines)
    ['A', 'B']
    """

def _testComponentReferences():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> font.componentReferences
    {'A': set(['C']), 'B': set(['C'])}
    >>> glyph = font["C"]
    >>> font.componentReferences
    {'A': set(['C']), 'B': set(['C'])}
    """

def _testBounds():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> font.bounds
    (0, 0, 700, 700)
    """

def _testControlPointBounds():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> font.controlPointBounds
    (0, 0, 700, 700)
    """

def _testSave():
    """
    >>> from defcon.test.testTools import makeTestFontCopy, tearDownTestFontCopy, getTestFontPath, getTestFontCopyPath
    >>> import glob
    >>> import os
    >>> path = makeTestFontCopy()
    >>> font = Font(path)
    >>> for glyph in font:
    ...     glyph.dirty = True
    >>> font.save()
    >>> fileNames = glob.glob(os.path.join(path, 'Glyphs', '*.glif'))
    >>> fileNames = [os.path.basename(fileName) for fileName in fileNames]
    >>> fileNames.sort()
    >>> fileNames
    ['A_.glif', 'B_.glif', 'C_.glif']
    >>> tearDownTestFontCopy()

    >>> path = getTestFontPath()
    >>> font = Font(path)
    >>> saveAsPath = getTestFontCopyPath(path)
    >>> font.save(saveAsPath)
    >>> fileNames = glob.glob(os.path.join(saveAsPath, 'Glyphs', '*.glif'))
    >>> fileNames = [os.path.basename(fileName) for fileName in fileNames]
    >>> fileNames.sort()
    >>> fileNames
    ['A_.glif', 'B_.glif', 'C_.glif']
    >>> font.path == saveAsPath
    True
    >>> tearDownTestFontCopy(saveAsPath)
    """

def _testGlyphNameChange():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.name = 'NameChangeTest'
    >>> keys = font.keys()
    >>> keys.sort()
    >>> keys
    ['B', 'C', 'NameChangeTest']
    >>> font.dirty
    True
    """

def _testGlyphUnicodesChanged():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.unicodes = [123, 456]
    >>> font.unicodeData[123]
    ['A']
    >>> font.unicodeData[456]
    ['A']
    >>> font.unicodeData[66]
    ['B']
    >>> font.unicodeData.get(65)

    >>> font = Font(getTestFontPath())
    >>> font.newGlyph("test")
    >>> glyph = font["test"]
    >>> glyph.unicodes = [65]
    >>> font.unicodeData[65]
    ['A', 'test']
    """

def _testTestForExternalChanges():
    """
    >>> from plistlib import readPlist, writePlist
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> font = Font(path)

    # load all the objects so that they get stamped
    >>> i = font.info
    >>> k = font.kerning
    >>> g = font.groups
    >>> l = font.lib
    >>> g = font["A"]

    >>> d = font.testForExternalChanges()
    >>> d["info"]
    False
    >>> d["kerning"]
    False
    >>> d["groups"]
    False
    >>> d["lib"]
    False
    >>> d["modifiedGlyphs"]
    []
    >>> d["addedGlyphs"]
    []
    >>> d["deletedGlyphs"]
    []

    # make a simple change to the kerning data
    >>> path = os.path.join(font.path, "kerning.plist")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t += " "
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    >>> os.utime(path, (k._dataOnDiskTimeStamp + 1, k._dataOnDiskTimeStamp + 1))

    >>> d = font.testForExternalChanges()
    >>> d["kerning"]
    True
    >>> d["info"]
    False

    # save the kerning data and test again
    >>> font.kerning.dirty = True
    >>> font.save()
    >>> d = font.testForExternalChanges()
    >>> d["kerning"]
    False

    # make a simple change to a glyph
    >>> path = os.path.join(font.path, "glyphs", "A_.glif")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t += " "
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    >>> os.utime(path, (g._dataOnDiskTimeStamp + 1, g._dataOnDiskTimeStamp + 1))
    >>> d = font.testForExternalChanges()
    >>> d["modifiedGlyphs"]
    ['A']

    # save the glyph and test again
    >>> font["A"].dirty = True
    >>> font.save()
    >>> d = font.testForExternalChanges()
    >>> d["modifiedGlyphs"]
    []

    # add a glyph
    >>> path = os.path.join(font.path, "glyphs", "A_.glif")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t = t.replace('<glyph name="A" format="1">', '<glyph name="XXX" format="1">')
    >>> path = os.path.join(font.path, "glyphs", "XXX.glif")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    >>> path = os.path.join(font.path, "glyphs", "contents.plist")
    >>> plist = readPlist(path)
    >>> savePlist = dict(plist)
    >>> plist["XXX"] = "XXX.glif"
    >>> writePlist(plist, path)
    >>> d = font.testForExternalChanges()
    >>> d["modifiedGlyphs"]
    []
    >>> d["addedGlyphs"]
    [u'XXX']

    # delete a glyph
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> font = Font(path)
    >>> g = font["XXX"]
    >>> path = os.path.join(font.path, "glyphs", "contents.plist")
    >>> writePlist(savePlist, path)
    >>> path = os.path.join(font.path, "glyphs", "XXX.glif")
    >>> os.remove(path)
    >>> d = font.testForExternalChanges()
    >>> d["modifiedGlyphs"]
    []
    >>> d["deletedGlyphs"]
    ['XXX']
    """

def _testReloadInfo():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> font = Font(path)
    >>> info = font.info

    >>> path = os.path.join(font.path, "fontinfo.plist")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t = t.replace("<integer>750</integer>", "<integer>751</integer>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()

    >>> info.ascender
    750
    >>> font.reloadInfo()
    >>> info.ascender
    751

    >>> t = t.replace("<integer>751</integer>", "<integer>750</integer>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    """

def _testReloadKerning():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> font = Font(path)
    >>> kerning = font.kerning

    >>> path = os.path.join(font.path, "kerning.plist")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t = t.replace("<integer>-100</integer>", "<integer>-101</integer>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()

    >>> kerning.items()
    [(('A', 'A'), -100)]
    >>> font.reloadKerning()
    >>> kerning.items()
    [(('A', 'A'), -101)]

    >>> t = t.replace("<integer>-101</integer>", "<integer>-100</integer>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    """

def _testReloadGroups():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> font = Font(path)
    >>> groups = font.groups

    >>> path = os.path.join(font.path, "groups.plist")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t = t.replace("<key>TestGroup</key>", "<key>XXX</key>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()

    >>> groups.keys()
    ['TestGroup']
    >>> font.reloadGroups()
    >>> groups.keys()
    ['XXX']

    >>> t = t.replace("<key>XXX</key>", "<key>TestGroup</key>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    """

def _testReloadLib():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> font = Font(path)
    >>> lib = font.lib

    >>> path = os.path.join(font.path, "lib.plist")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t = t.replace("<key>org.robofab.glyphOrder</key>", "<key>org.robofab.glyphOrder.XXX</key>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()

    >>> lib.keys()
    ['org.robofab.glyphOrder']
    >>> font.reloadLib()
    >>> lib.keys()
    ['org.robofab.postScriptHintData', 'org.robofab.glyphOrder.XXX']

    >>> t = t.replace("<key>org.robofab.glyphOrder.XXX</key>", "<key>org.robofab.glyphOrder</key>")
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    """

def _testReloadGlyphs():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> path = getTestFontPath("TestExternalEditing.ufo")
    >>> font = Font(path)
    >>> glyph = font["A"]

    >>> path = os.path.join(font.path, "glyphs", "A_.glif")
    >>> f = open(path, "rb")
    >>> t = f.read()
    >>> f.close()
    >>> t = t.replace('<advance width="700"/>', '<advance width="701"/>')
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()

    >>> glyph.width
    700
    >>> len(glyph)
    2
    >>> font.reloadGlyphs(["A"])
    >>> glyph.width
    701
    >>> len(glyph)
    2

    >>> t = t.replace('<advance width="701"/>', '<advance width="700"/>')
    >>> f = open(path, "wb")
    >>> f.write(t)
    >>> f.close()
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
