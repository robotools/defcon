from fontTools.misc import arrayTools
from defcon.objects.base import BaseObject
from defcon.objects.contour import Contour
from defcon.objects.point import Point
from defcon.objects.component import Component
from defcon.objects.anchor import Anchor
from defcon.objects.lib import Lib
from defcon.objects.guideline import Guideline
from defcon.objects.image import Image
from defcon.tools.notifications import NotificationCenter

_representationFactories = {}

def addRepresentationFactory(name, factory):
    _representationFactories[name] = factory

def removeRepresentationFactory(name):
    del _representationFactories[name]


class Glyph(BaseObject):

    """
    This object represents a glyph and it contains contour, component, anchor
    and other assorted bits data about the glyph.

    **This object posts the following notifications:**

    =====================  ====
    Name                   Note
    =====================  ====
    Glyph.Changed          Posted when the *dirty* attribute is set.
    Glyph.NameChanged      Posted after the *reloadGlyphs* method has been called.
    Glyph.UnicodesChanged  Posted after the *reloadGlyphs* method has been called.
    =====================  ====

    The Glyph object has list like behavior. This behavior allows you to interact
    with contour data directly. For example, to get a particular contour::

        contour = glyph[0]

    To iterate over all contours::

        for contour in glyph:

    To get the number of contours::

        contourCount = len(glyph)

    To interact with components or anchors in a similar way,
    use the ``components`` and ``anchors`` attributes.
    """

    changeNotificationName = "Glyph.Changed"

    def __init__(self, contourClass=None, pointClass=None, componentClass=None, anchorClass=None, guidelineClass=None, libClass=None):
        super(Glyph, self).__init__()

        self._parent = None
        self._dirty = False
        self._name = None
        self._unicodes = []
        self._width = 0
        self._height = 0
        self._note = None
        self._image = None
        self._identifiers = set()
        self._contours = []
        self._components = []
        self._anchors = []
        self._guidelines = []
        self._lib = None
        self._boundsCache = None
        self._controlPointBoundsCache = None
        self._representations = {}

        if contourClass is None:
            contourClass = Contour
        if pointClass is None:
            pointClass = Point
        if componentClass is None:
            componentClass = Component
        if anchorClass is None:
            anchorClass = Anchor
        if guidelineClass is None:
            guidelineClass = Guideline
        if libClass is None:
            libClass = Lib

        self._contourClass = contourClass
        self._pointClass = pointClass
        self._componentClass = componentClass
        self._anchorClass = anchorClass
        self._guidelineClass = Guideline
        self._lib = libClass()

    def setParent(self, obj):
        if obj is None:
            if self.getParent() is not None:
                for contour in self._contours:
                    self._removeParentDataInContour(contour)
                for component in self._components:
                    self._removeParentDataInComponent(component)
                for anchor in self._anchors:
                    self._removeParentDataInAnchor(anchor)
                for guideline in self._guidelines:
                    self._removeParentDataInGuideline(guideline)
                self._removeParentDataInLib()
                self._removeParentDataInImage()
                self.removeObserver(observer=self, notification="Glyph.Changed")
                super(Glyph, self).setParent(obj)
        else:
            assert self.getParent() is None
            super(Glyph, self).setParent(obj)
            for contour in self._contours:
                self._setParentDataInContour(contour)
            for component in self._components:
                self._setParentDataInComponent(component)
            for anchor in self._anchors:
                self._setParentDataInAnchor(anchor)
            for guideline in self._guidelines:
                self._setParentDataInGuideline(guideline)
            self._setParentDataInLib()
            self._setParentDataInImage()
            self.addObserver(observer=self, methodName="destroyAllRepresentations", notification="Glyph.Changed")

    def _destroyBoundsCache(self):
        self._boundsCache = None
        self._controlPointBoundsCache = None

    # ----------
    # Attributes
    # ----------

    def _get_contourClass(self):
        return self._contourClass

    contourClass = property(_get_contourClass, doc="The class used for contours.")

    def _get_pointClass(self):
        return self._pointClass

    pointClass = property(_get_pointClass, doc="The class used for points.")

    def _get_componentClass(self):
        return self._componentClass

    componentClass = property(_get_componentClass, doc="The class used for components.")

    def _get_anchorClass(self):
        return self._anchorClass

    anchorClass = property(_get_anchorClass, doc="The class used for anchors.")

    def _get_guidelineClass(self):
        return self._guidelineClass

    guidelineClass = property(_get_guidelineClass, doc="The class used for anchors.")

    def _get_identifiers(self):
        return self._identifiers

    identifiers = property(_get_identifiers, doc="Set of identifiers for the glyph. This is primarily for internal use.")

    def _set_name(self, value):
        oldName = self._name
        if oldName != value:
            self._name = value
            self.dirty = True
            data = dict(oldName=oldName, newName=value)
            self.postNotification(notification="Glyph.NameChanged", data=data)

    def _get_name(self):
        return self._name

    name = property(_get_name, _set_name, doc="The name of the glyph. Setting this posts a *Glyph.NameChanged* notification.")

    def _get_unicodes(self):
        return list(self._unicodes)

    def _set_unicodes(self, value):
        oldValue = self.unicodes
        if oldValue != value:
            self._unicodes = value
            self.dirty = True
            data = dict(oldValues=oldValue, newValues=value)
            self.postNotification(notification="Glyph.UnicodesChanged", data=data)

    unicodes = property(_get_unicodes, _set_unicodes, doc="The list of unicode values assigned to the glyph. Setting this posts *Glyph.UnicodesChanged* and *Glyph.Changed* notifications.")

    def _get_unicode(self):
        if self._unicodes:
            return self._unicodes[0]
        return None

    def _set_unicode(self, value):
        if value is None:
            self.unicodes = []
        else:
            existing = list(self._unicodes)
            if value in existing:
                existing.pop(existing.index(value))
            existing.insert(0, value)
            self.unicodes = existing

    unicode = property(_get_unicode, _set_unicode, doc="The primary unicode value for the glyph. This is the equivalent of ``glyph.unicodes[0]``. This is a convenience attribute that works with the ``unicodes`` attribute.")

    def _get_bounds(self):
        from robofab.pens.boundsPen import BoundsPen
        if self._boundsCache is None:
            pen = BoundsPen(self.getParent())
            self.draw(pen)
            self._boundsCache = pen.bounds
        return self._boundsCache

    bounds = property(_get_bounds, doc="The bounds of the glyph's outline expressed as a tuple of form (xMin, yMin, xMax, yMax).")

    def _get_controlPointBounds(self):
        from fontTools.pens.boundsPen import ControlBoundsPen
        if self._controlPointBoundsCache is None:
            pen = ControlBoundsPen(self.getParent())
            self.draw(pen)
            self._controlPointBoundsCache = pen.bounds
        return self._controlPointBoundsCache

    controlPointBounds = property(_get_controlPointBounds, doc="The control bounds of all points in the glyph. This only measures the point positions, it does not measure curves. So, curves without points at the extrema will not be properly measured.")

    def _get_leftMargin(self):
        bounds = self.bounds
        if bounds is None:
            return None
        xMin, yMin, xMax, yMax = bounds
        return xMin

    def _set_leftMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        xMin, yMin, xMax, yMax = bounds
        diff = value - xMin
        self.move((diff, 0))
        self._width += diff
        self.dirty = True

    leftMargin = property(_get_leftMargin, _set_leftMargin, doc="The left margin of the glyph. Setting this posts a *Glyph.Changed* notification.")

    def _get_rightMargin(self):
        bounds = self.bounds
        if bounds is None:
            return None
        xMin, yMin, xMax, yMax = bounds
        return self._width - xMax

    def _set_rightMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        xMin, yMin, xMax, yMax = bounds
        self._width = xMax + value
        self.dirty = True

    rightMargin = property(_get_rightMargin, _set_rightMargin, doc="The right margin of the glyph. Setting this posts a *Glyph.Changed* notification.")

    def _get_width(self):
        return self._width

    def _set_width(self, value):
        self._width = value
        self.dirty = True

    width = property(_get_width, _set_width, doc="The width of the glyph. Setting this posts a *Glyph.Changed* notification.")

    def _get_height(self):
        return self._height

    def _set_height(self, value):
        self._height = value
        self.dirty = True

    height = property(_get_height, _set_height, doc="The height of the glyph. Setting this posts a *Glyph.Changed* notification.")

    def _get_components(self):
        return list(self._components)

    components = property(_get_components, doc="An ordered list of :class:`Component` objects stored in the glyph.")

    def _get_anchors(self):
        return list(self._anchors)

    def _set_anchors(self, value):
        self.clearAnchors()
        self.holdNotifications()
        for anchor in value:
            self.appendAnchor(anchor)
        self.releaseHeldNotifications()

    anchors = property(_get_anchors, _set_anchors, doc="An ordered list of :class:`Anchor` objects stored in the glyph.")

    def _get_guidelines(self):
        return list(self._guidelines)

    def _set_guidelines(self, value):
        self.clearGuidelines()
        self.holdNotifications()
        for guideline in value:
            self.appendGuideline(guideline)
        self.releaseHeldNotifications()

    guidelines = property(_get_guidelines, _set_guidelines, doc="An ordered list of :class:`Guideline` objects stored in the glyph. Setting this will post a *Glyph.Changed* notification along with any notifications posted by the :py:meth:`Glyph.appendGuideline` and :py:meth:`Glyph.clearGuidelines` methods.")

    def _get_note(self):
        return self._note

    def _set_note(self, value):
        if value is not None:
            assert isinstance(value, basestring)
        self._note = value
        self.dirty = True

    note = property(_get_note, _set_note, doc="An arbitrary note for the glyph. Setting this will post a *Glyph.Changed* notification.")

    def _get_lib(self):
        return self._lib

    def _set_lib(self, value):
        self._lib.clear()
        self._lib.update(value)
        self.dirty = True

    lib = property(_get_lib, _set_lib, doc="The glyph's :class:`Lib` object. Setting this will clear any existing lib data and post a *Glyph.Changed* notification if data was replaced.")

    def _get_image(self):
        return self._image

    def _set_image(self, image):
        if image is None:
            if self._image is not None:
                self._removeParentDataInImage()
                self._image = None
                self.dirty = True
        else:
            if self._image is None:
                self._image = Image()
                self._setParentDataInImage()
            if set(self.image.items()) != set(image.items()):
                for key in self._image.keys():
                    self._image[key] = image.get(key)
                self.dirty = True

    image = property(_get_image, _set_image, doc="The glyph's :class:`Image` object. Setting this will post a *Glyph.Changed* notification.")

    # -----------
    # Pen Methods
    # -----------

    def draw(self, pen):
        """
        Draw the glyph with **pen**.
        """
        from robofab.pens.adapterPens import PointToSegmentPen
        pointPen = PointToSegmentPen(pen)
        self.drawPoints(pointPen)

    def drawPoints(self, pointPen):
        """
        Draw the glyph with **pointPen**.
        """
        for contour in self._contours:
            contour.drawPoints(pointPen)
        for component in self._components:
            component.drawPoints(pointPen)

    def getPen(self):
        """
        Get the pen used to draw into this glyph.
        """
        from robofab.pens.adapterPens import SegmentToPointPen
        return SegmentToPointPen(self.getPointPen())

    def getPointPen(self):
        """
        Get the point pen used to draw into this glyph.
        """
        from defcon.pens.glyphObjectPointPen import GlyphObjectPointPen
        return GlyphObjectPointPen(self)

    # --------------------------
    # Parent Setting and Removal
    # --------------------------

    def _setParentDataInLib(self):
        self._lib.setParent(self)
        if self.dispatcher is not None and not self._lib.hasObserver(observer=self, notification="Lib.Changed"):
            self._lib.addObserver(observer=self, methodName="_libContentChanged", notification="Lib.Changed")

    def _removeParentDataInLib(self):
        if self.dispatcher is not None:
            self._lib.removeObserver(observer=self, notification="Lib.Changed")
        self._lib.setParent(None)

    def _setParentDataInContour(self, contour):
        contour.setParent(self)
        if self.dispatcher is not None and not contour.hasObserver(observer=self, notification="Contour.Changed"):
            contour.addObserver(observer=self, methodName="_outlineContentChanged", notification="Contour.Changed")

    def _removeParentDataInContour(self, contour):
        if self.dispatcher is not None:
            contour.removeObserver(observer=self, notification="Contour.Changed")
        contour.setParent(None)

    def _setParentDataInComponent(self, component):
        component.setParent(self)
        if self.dispatcher is not None and not component.hasObserver(observer=self, notification="Component.Changed"):
            component.addObserver(observer=self, methodName="_outlineContentChanged", notification="Component.Changed")

    def _removeParentDataInComponent(self, component):
        if self.dispatcher is not None:
            component.removeObserver(observer=self, notification="Component.Changed")
        component.setParent(None)

    def _setParentDataInAnchor(self, anchor):
        anchor.setParent(self)
        if self.dispatcher is not None and not anchor.hasObserver(observer=self, notification="Anchor.Changed"):
            anchor.addObserver(observer=self, methodName="_outlineContentChanged", notification="Anchor.Changed")

    def _removeParentDataInAnchor(self, anchor):
        if self.dispatcher is not None:
            anchor.removeObserver(observer=self, notification="Anchor.Changed")
        anchor.setParent(None)

    def _setParentDataInGuideline(self, guideline):
        guideline.setParent(self)
        if self.dispatcher is not None and not guideline.hasObserver(observer=self, notification="Guideline.Changed"):
            guideline.addObserver(observer=self, methodName="_guidelineChanged", notification="Guideline.Changed")

    def _removeParentDataInGuideline(self, guideline):
        if self.dispatcher is not None:
            guideline.removeObserver(observer=self, notification="Guideline.Changed")
        guideline.setParent(None)

    def _setParentDataInImage(self):
        if self._image is None:
            return
        self._image.setParent(self)
        if self.dispatcher is not None and not self._image.hasObserver(observer=self, notification="Image.Changed"):
            self._image.addObserver(observer=self, methodName="_imageChanged", notification="Image.Changed")

    def _removeParentDataInImage(self):
        if self._image is None:
            return
        if self.dispatcher is not None:
            self._image.removeObserver(observer=self, notification="Image.Changed")
        self._image.setParent(None)

    # -------
    # Methods
    # -------

    def __len__(self):
        return len(self._contours)

    def __iter__(self):
        contourCount = len(self)
        index = 0
        while index < contourCount:
            contour = self[index]
            yield contour
            index += 1

    def __getitem__(self, index):
        return self._contours[index]

    def _getContourIndex(self, contour):
        return self._contours.index(contour)

    def copyDataFromGlyph(self, glyph):
        """
        Copy data from **glyph**. This copies the following data:

        ==========
        width
        height
        unicodes
        note
        image
        contours
        components
        anchors
        guidelines
        lib
        ==========

        The name attribute is purposefully omitted.
        """
        from copy import deepcopy
        self.width = glyph.width
        self.height = glyph.height
        self.unicodes = list(glyph.unicodes)
        self.note = glyph.note
        self.guidelines = glyph.guidelines
        self.anchors = glyph.anchors
        self.image = glyph.image
        pointPen = self.getPointPen()
        glyph.drawPoints(pointPen)
        self.lib = deepcopy(glyph.lib)

    def appendContour(self, contour):
        """
        Append **contour** to the glyph. The contour must be a defcon
        :class:`Contour` object or a subclass of that object. An error
        will be raised if the contour's identifier or a point identifier
        conflicts with any of the identifiers within the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert contour not in self._contours
        self.insertContour(len(self._contours), contour)

    def appendComponent(self, component):
        """
        Append **component** to the glyph. The component must be a defcon
        :class:`Component` object or a subclass of that object. An error
        will be raised if the component's identifier conflicts with any of
        the identifiers within the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert component not in self._components
        self.insertComponent(len(self._components), component)

    def appendAnchor(self, anchor):
        """
        Append **anchor** to the glyph. The anchor must be a defcon
        :class:`Anchor` object or a subclass of that object. An error
        will be raised if the anchor's identifier conflicts with any of
        the identifiers within the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert anchor not in self._anchors
        self.insertAnchor(len(self._anchors), anchor)

    def appendGuideline(self, guideline):
        """
        Append **guideline** to the glyph. The guideline must be a defcon
        :class:`Guideline` object or a subclass of that object. An error
        will be raised if the guideline's identifier conflicts with any of
        the identifiers within the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert guideline not in self._guidelines
        self.insertGuideline(len(self._guidelines), guideline)

    def insertContour(self, index, contour):
        """
        Insert **contour** into the glyph at index. The contour
        must be a defcon :class:`Contour` object or a subclass
        of that object. An error will be raised if the contour's
        identifier or a point identifier conflicts with any of
        the identifiers within the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert contour not in self._contours
        identifiers = self._identifiers
        if contour.identifier is not None:
            assert contour.identifier not in identifiers
            if contour.identifier is not None:
                identifiers.add(contour.identifier)
        for point in contour:
            if point.identifier is not None:
                assert point.identifier not in identifiers
                self._identifiers.add(point.identifier)
        if contour.getParent() != self:
            self._setParentDataInContour(contour)
        self._contours.insert(index, contour)
        self._destroyBoundsCache()
        self.dirty = True

    def insertComponent(self, index, component):
        """
        Insert **component** into the glyph at index. The component
        must be a defcon :class:`Component` object or a subclass
        of that object. An error will be raised if the component's
        identifier conflicts with any of the identifiers within
        the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert component not in self._components
        if component.identifier is not None:
            identifiers = self._identifiers
            assert component.identifier not in identifiers
            if component.identifier is not None:
                identifiers.add(component.identifier)
        if component.getParent() != self:
            self._setParentDataInComponent(component)
        self._components.insert(index, component)
        self._destroyBoundsCache()
        self.dirty = True

    def insertAnchor(self, index, anchor):
        """
        Insert **anchor** into the glyph at index. The anchor
        must be a defcon :class:`Anchor` object or a subclass
        of that object. An error will be raised if the anchor's
        identifier conflicts with any of the identifiers within
        the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert anchor not in self._anchors
        if not isinstance(anchor, self._anchorClass):
            anchor = self._anchorClass(anchor)
        if anchor.identifier is not None:
            identifiers = self._identifiers
            assert anchor.identifier not in identifiers
            if anchor.identifier is not None:
                identifiers.add(anchor.identifier)
        if anchor.getParent() != self:
            self._setParentDataInAnchor(anchor)
        self._anchors.insert(index, anchor)
        self.dirty = True

    def insertGuideline(self, index, guideline):
        """
        Insert **guideline** into the glyph at index. The guideline
        must be a defcon :class:`Guideline` object or a subclass
        of that object. An error will be raised if the guideline's
        identifier conflicts with any of the identifiers within
        the glyph.

        This will post a *Glyph.Changed* notification.
        """
        assert guideline not in self._guidelines
        if not isinstance(guideline, self._guidelineClass):
            guideline = self._guidelineClass(guideline)
        if guideline.identifier is not None:
            identifiers = self._identifiers
            assert guideline.identifier not in identifiers
            if guideline.identifier is not None:
                identifiers.add(guideline.identifier)
        if guideline.getParent() != self:
            self._setParentDataInGuideline(guideline)
        self._guidelines.insert(index, guideline)
        self.dirty = True

    def removeContour(self, contour):
        """
        Remove **contour** from the glyph.

        This will post a *Glyph.Changed* notification.
        """
        identifiers = self._identifiers
        if contour.identifier is not None:
            identifiers.remove(contour.identifier)
        for point in contour:
            if point.identifier is not None:
                identifiers.remove(point.identifier)
        self._contours.remove(contour)
        self._removeParentDataInContour(contour)
        self._destroyBoundsCache()
        self.dirty = True

    def removeComponent(self, component):
        """
        Remove **component** from the glyph.

        This will post a *Glyph.Changed* notification.
        """
        if component.identifier is not None:
            self._identifiers.remove(component.identifier)
        self._components.remove(component)
        self._removeParentDataInComponent(component)
        self._destroyBoundsCache()
        self.dirty = True

    def removeAnchor(self, anchor):
        """
        Remove **anchor** from the glyph.

        This will post a *Glyph.Changed* notification.
        """
        # XXX handle identifiers
        self._anchors.remove(anchor)
        self._removeParentDataInAnchor(anchor)
        self.dirty = True

    def removeGuideline(self, guideline):
        """
        Remove **guideline** from the glyph.

        This will post a *Glyph.Changed* notification.
        """
        if guideline.identifier is not None:
            self._identifiers.remove(guideline.identifier)
        self._guidelines.remove(guideline)
        self._removeParentDataInGuideline(guideline)
        self.dirty = True

    def contourIndex(self, contour):
        """
        Get the index for **contour**.
        """
        return self._contours.index(contour)

    def componentIndex(self, component):
        """
        Get the index for **component**.
        """
        return self._components.index(component)

    def anchorIndex(self, anchor):
        """
        Get the index for **anchor**.
        """
        return self._anchors.index(anchor)

    def guidelineIndex(self, guideline):
        """
        Get the index for **guideline**.
        """
        return self._guidelines.index(guideline)

    def clear(self):
        """
        Clear all contours, components, anchors and guidelines from the glyph.

        This posts a *Glyph.Changed* notification.
        """
        self.holdNotifications()
        self.clearContours()
        self.clearComponents()
        self.clearAnchors()
        self.clearGuidelines()
        self.releaseHeldNotifications()

    def clearContours(self):
        """
        Clear all contours from the glyph.

        This posts a *Glyph.Changed* notification.
        """
        self.holdNotifications()
        for contour in reversed(self._contours):
            self.removeContour(contour)
        self.releaseHeldNotifications()

    def clearComponents(self):
        """
        Clear all components from the glyph.

        This posts a *Glyph.Changed* notification.
        """
        self.holdNotifications()
        for component in reversed(self._components):
            self.removeComponent(component)
        self.releaseHeldNotifications()

    def clearAnchors(self):
        """
        Clear all anchors from the glyph.

        This posts a *Glyph.Changed* notification.
        """
        self.holdNotifications()
        for anchor in reversed(self._anchors):
            self.removeAnchor(anchor)
        self.releaseHeldNotifications()

    def clearGuidelines(self):
        """
        Clear all guidelines from the glyph.

        This posts a *Glyph.Changed* notification.
        """
        self.holdNotifications()
        for guideline in reversed(self._guidelines):
            self.removeGuideline(guideline)
        self.releaseHeldNotifications()

    def move(self, (x, y)):
        """
        Move all contours, components and anchors in the glyph
        by **(x, y)**.

        This posts a *Glyph.Changed* notification.
        """
        oldBounds = self._boundsCache
        oldControlPointBounds = self._controlPointBoundsCache
        for contour in self._contours:
            contour.move((x, y))
        for component in self._components:
            component.move((x, y))
        for anchor in self._anchors:
            anchor.move((x, y))
        if oldBounds:
            xMin, yMin, xMax, yMax = oldBounds
            xMin += x
            yMin += y
            xMax += x
            yMax += y
            self._boundsCache = (xMin, yMin, xMax, yMax)
        if oldControlPointBounds:
            xMin, yMin, xMax, yMax = oldControlPointBounds
            xMin += x
            yMin += y
            xMax += x
            yMax += y
            self._controlPointBoundsCache = (xMin, yMin, xMax, yMax)

    def pointInside(self, (x, y), evenOdd=False):
        """
        Returns a boolean indicating if **(x, y)** is in the
        "black" area of the glyph.
        """
        from fontTools.pens.pointInsidePen import PointInsidePen
        pen = PointInsidePen(glyphSet=None, testPoint=(x, y), evenOdd=evenOdd)
        self.draw(pen)
        return pen.getResult()

    # ---------------
    # Representations
    # ---------------

    def representationKeys(self):
        """
        Get a list of all representation keys
        that have been called within this object.
        """
        representations = []
        for key in self._representations.keys():
            if isinstance(key, basestring):
                name = key
                kwargs = {}
            else:
                name = key[0]
                kwargs = {}
                for k, v in key[1:]:
                    kwargs[k] = v
            representations.append((name, kwargs))
        return representations

    def destroyRepresentation(self, name, **kwargs):
        """
        Destroy the stored representation for **name**
        and **\*\*kwargs**.
        """
        key = self._makeRepresentationKey(name, **kwargs)
        if key in self._representations:
            del self._representations[key]

    def destroyAllRepresentations(self, notification=None):
        """
        Destroy all representations.
        """
        self._representations = {}

    def getRepresentation(self, name, **kwargs):
        """
        Get a representation. **name** must be a registered
        representation name. **\*\*kwargs** will be passed
        to the appropriate representation factory.
        """
        key = self._makeRepresentationKey(name, **kwargs)
        if key not in self._representations:
            factory = _representationFactories[name]
            representation = factory(self, self.getParent(), **kwargs)
            self._representations[key] = representation
        return self._representations[key]

    def hasCachedRepresentation(self, name, **kwargs):
        """
        Returns a boolean indicating if a representation for
        **name** and **\*\*kwargs** is cahced in the glyph.
        """
        key = self._makeRepresentationKey(name, **kwargs)
        return key in self._representations

    def _makeRepresentationKey(self, name, **kwargs):
        if kwargs:
            key = [name] + sorted(kwargs.items())
            key = tuple(key)
        else:
            key = name
        return key

    # ----------------------
    # Notification Callbacks
    # ----------------------

    def _imageChanged(self, notification):
        self.dirty = True

    def _outlineContentChanged(self, notification):
        self._destroyBoundsCache()
        self.dirty = True

    def _guidelineChanged(self, notification):
        self.dirty = True

    def _libContentChanged(self, notification):
        self.dirty = True


# -----
# Tests
# -----

def _testName():
    """
    # set
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.name = 'RenamedGlyph'
    >>> glyph.name
    'RenamedGlyph'
    >>> keys = font.keys()
    >>> keys.sort()
    >>> keys
    ['B', 'C', 'RenamedGlyph']

    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.name = 'A'
    >>> glyph.dirty
    False

    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.name
    'A'
    """

def _testUnicodes():
    """
    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.unicodes
    [65]

    # set
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.unicodes = [123, 456]
    >>> glyph.unicodes
    [123, 456]
    >>> glyph.dirty
    True
    """

def _testBounds():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.bounds
    (0, 0, 700, 700)
    >>> glyph = font['B']
    >>> glyph.bounds
    (0, 0, 700, 700)
    >>> glyph = font['C']
    >>> glyph.bounds
    (0.0, 0.0, 700.0, 700.0)
    """

def _testControlPointBounds():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.controlPointBounds
    (0, 0, 700, 700)
    >>> glyph = font['B']
    >>> glyph.controlPointBounds
    (0, 0, 700, 700)
    >>> glyph = font['C']
    >>> glyph.controlPointBounds
    (0.0, 0.0, 700.0, 700.0)
    """

def _testLeftMargin():
    """
    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.leftMargin
    0
    >>> glyph = font['B']
    >>> glyph.leftMargin
    0

    # set
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.leftMargin = 100
    >>> glyph.leftMargin
    100
    >>> glyph.width
    800
    >>> glyph.dirty
    True
    """

def _testRightMargin():
    """
    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.rightMargin
    0

    # set
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.rightMargin = 100
    >>> glyph.rightMargin
    100
    >>> glyph.width
    800
    >>> glyph.dirty
    True
    """

def _testWidth():
    """
    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.width
    700

    # set
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.width = 100
    >>> glyph.width
    100
    >>> glyph.dirty
    True
    """

def _testHeight():
    """
    # get
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.height
    500

    # set
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.height = 100
    >>> glyph.height
    100
    >>> glyph.dirty
    True
    """

def _testComponents():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['C']
    >>> len(glyph.components)
    2
    """

def _testAnchors():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> len(glyph.anchors)
    2
    """

def _testCopyFromGlyph():
    """
    >>> source = Glyph()
    >>> source.name = "a"
    >>> source.width = 1
    >>> source.height = 2
    >>> source.unicodes = [3, 4]
    >>> source.note = "test image"
    >>> source.image = dict(fileName="test image")
    >>> source.anchors = [dict(x=100, y=200, name="test anchor")]
    >>> source.guidelines = [dict(x=10, y=20, name="test guideline")]
    >>> source.lib = {"foo" : "bar"}
    >>> pen = source.getPointPen()
    >>> pen.beginPath()
    >>> pen.addPoint((100, 200), segmentType="line")
    >>> pen.addPoint((300, 400), segmentType="line")
    >>> pen.endPath()
    >>> component = Component()
    >>> component.base = "b"
    >>> source.appendComponent(component)
    >>> dest = Glyph()
    >>> dest.copyDataFromGlyph(source)

    >>> source.name == dest.name
    False
    >>> source.width == dest.width
    True
    >>> source.height == dest.height
    True
    >>> source.unicodes == dest.unicodes
    True
    >>> source.note == dest.note
    True
    >>> source.image.items() == dest.image.items()
    True
    >>> [g.items() for g in source.guidelines] == [g.items() for g in dest.guidelines]
    True
    >>> [g.items() for g in source.anchors] == [g.items() for g in dest.anchors]
    True
    >>> len(source) == len(dest)
    True
    >>> len(source.components) == len(dest.components)
    True
    >>> sourceContours = []
    >>> for contour in source:
    ...     sourceContours.append([])
    ...     for point in contour:
    ...         sourceContours[-1].append((point.x, point.x, point.segmentType, point.name))
    >>> destContours = []
    >>> for contour in dest:
    ...     destContours.append([])
    ...     for point in contour:
    ...         destContours[-1].append((point.x, point.x, point.segmentType, point.name))
    >>> sourceContours == destContours
    True
    >>> source.components[0].baseGlyph == dest.components[0].baseGlyph
    True
    """

def _testLen():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> len(glyph)
    2
    """

def _testIter():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> for contour in glyph:
    ...     print len(contour)
    4
    4
    """

def _testAppendContour():
    """
    >>> from defcon.objects.contour import Contour
    >>> glyph = Glyph()
    >>> glyph.dirty = False
    >>> contour = Contour()
    >>> glyph.appendContour(contour)
    >>> len(glyph)
    1
    >>> glyph.dirty
    True
    >>> contour.getParent() == glyph
    True
    """

def _testAppendComponent():
    """
    >>> from defcon.objects.component import Component
    >>> glyph = Glyph()
    >>> glyph.dirty = False
    >>> component = Component()
    >>> glyph.appendComponent(component)
    >>> len(glyph.components)
    1
    >>> glyph.dirty
    True
    >>> component.getParent() == glyph
    True
    """

def _testAppendAnchor():
    """
    >>> from defcon.objects.anchor import Anchor
    >>> glyph = Glyph()
    >>> glyph.dirty = False
    >>> anchor = Anchor()
    >>> glyph.appendAnchor(anchor)
    >>> len(glyph.anchors)
    1
    >>> glyph.dirty
    True
    >>> anchor.getParent() == glyph
    True
    """

def _testAppendGuideline():
    """
    >>> from defcon.objects.guideline import Guideline
    >>> glyph = Glyph()
    >>> glyph.dirty = False
    >>> guideline = Guideline()
    >>> glyph.appendGuideline(guideline)
    >>> len(glyph.guidelines)
    1
    >>> glyph.dirty
    True
    >>> guideline.getParent() == glyph
    True
    """

def _testRemoveContour():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> contour = glyph[0]
    >>> glyph.removeContour(contour)
    >>> contour in glyph._contours
    False
    >>> contour.getParent()
    """

def _testRemoveComponent():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['C']
    >>> component = glyph.components[0]
    >>> glyph.removeComponent(component)
    >>> component in glyph.components
    False
    >>> component.getParent()
    """

def _testRemoveAnchor():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> anchor = glyph.anchors[0]
    >>> glyph.removeAnchor(anchor)
    >>> anchor in glyph.anchors
    False
    >>> anchor.getParent()
    """

def _testRemoveGuideline():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font.layers["Layer 1"]["A"]
    >>> guideline = glyph.guidelines[0]
    >>> glyph.removeGuideline(guideline)
    >>> guideline in glyph.guidelines
    False
    >>> guideline.getParent()
    """

def _testContourIndex():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> contour = glyph[0]
    >>> glyph.contourIndex(contour)
    0
    >>> contour = glyph[1]
    >>> glyph.contourIndex(contour)
    1
    """

def _testComponentIndex():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['C']
    >>> component = glyph.components[0]
    >>> glyph.componentIndex(component)
    0
    >>> component = glyph.components[1]
    >>> glyph.componentIndex(component)
    1
    """

def _testAnchorIndex():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> anchor = glyph.anchors[0]
    >>> glyph.anchorIndex(anchor)
    0
    >>> anchor = glyph.anchors[1]
    >>> glyph.anchorIndex(anchor)
    1
    """

def _testClear():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> contour = glyph[0]
    >>> anchor = glyph.anchors[0]
    >>> glyph.clear()
    >>> len(glyph)
    0
    >>> len(glyph.anchors)
    0
    >>> glyph = font['C']
    >>> component = glyph.components[0]
    >>> glyph.clear()
    >>> len(glyph.components)
    0
    >>> glyph = font.layers["Layer 1"]["A"]
    >>> guideline = glyph.guidelines[0]
    >>> glyph.clear()
    >>> len(glyph.guidelines)
    0

    >>> contour.getParent(), component.getParent(), anchor.getParent(), guideline.getParent()
    (None, None, None, None)
    >>> contour.dispatcher, component.dispatcher, anchor.dispatcher, guideline.dispatcher
    (None, None, None, None)
    """

def _testClearContours():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.clearContours()
    >>> len(glyph)
    0
    """

def _testClearComponents():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['C']
    >>> glyph.clearComponents()
    >>> len(glyph.components)
    0
    """

def _testClearAnchors():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.clearAnchors()
    >>> len(glyph.anchors)
    0
    """

def _testClearGuidelines():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.clearGuidelines()
    >>> len(glyph.guidelines)
    0
    """

def _testMove():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> xMin, yMin, xMax, yMax = glyph.bounds
    >>> glyph.move((100, 50))
    >>> (xMin+100, yMin+50, xMax+100, yMax+50) == glyph.bounds
    True
    >>> glyph = font['C']
    >>> xMin, yMin, xMax, yMax = glyph.bounds

    #>>> glyph.move((100, 50))
    #>>> (xMin+100, yMin+50, xMax+100, yMax+50) == glyph.bounds
    #True
    """

def _testPointInside():
    """
    >>> from defcon.test.testTools import getTestFontPath
    >>> from defcon.objects.font import Font
    >>> font = Font(getTestFontPath())
    >>> glyph = font['A']
    >>> glyph.pointInside((100, 100))
    True
    >>> glyph.pointInside((350, 350))
    False
    >>> glyph.pointInside((-100, -100))
    False
    """

def _testIdentifiers():
    """
    >>> glyph = Glyph()
    >>> pointPen = glyph.getPointPen()
    >>> pointPen.beginPath(identifier="contour 1")
    >>> pointPen.addPoint((0, 0), identifier="point 1")
    >>> pointPen.addPoint((0, 0), identifier="point 2")
    >>> pointPen.endPath()
    >>> pointPen.beginPath(identifier="contour 2")
    >>> pointPen.endPath()
    >>> pointPen.addComponent("A", (1, 1, 1, 1, 1, 1), identifier="component 1")
    >>> pointPen.addComponent("A", (1, 1, 1, 1, 1, 1), identifier="component 2")
    >>> guideline = Guideline()
    >>> guideline.identifier = "guideline 1"
    >>> glyph.appendGuideline(guideline)
    >>> guideline = Guideline()
    >>> guideline.identifier = "guideline 2"
    >>> glyph.appendGuideline(guideline)

    >>> for contour in glyph:
    ...     contour.identifier
    'contour 1'
    'contour 2'
    >>> for point in glyph[0]:
    ...     point.identifier
    'point 1'
    'point 2'
    >>> for component in glyph.components:
    ...     component.identifier
    'component 1'
    'component 2'

    >>> pointPen.beginPath(identifier="contour 1")
    >>> pointPen.endPath()
    Traceback (most recent call last):
        ...
    AssertionError

    >>> pointPen.beginPath()
    >>> pointPen.addPoint((0, 0))
    >>> pointPen.addPoint((0, 0), identifier="point 1")
    >>> pointPen.endPath()
    Traceback (most recent call last):
        ...
    AssertionError

    >>> pointPen.addComponent("A", (1, 1, 1, 1, 1, 1), identifier="component 1")
    Traceback (most recent call last):
        ...
    AssertionError

    >>> g = Guideline()
    >>> g.identifier = "guideline 1"
    >>> glyph.appendGuideline(g)
    Traceback (most recent call last):
        ...
    AssertionError

    >>> list(sorted(glyph.identifiers))
    ['component 1', 'component 2', 'contour 1', 'contour 2', 'guideline 1', 'guideline 2', 'point 1', 'point 2']
    >>> glyph.removeContour(glyph[0])
    >>> list(sorted(glyph.identifiers))
    ['component 1', 'component 2', 'contour 2', 'guideline 1', 'guideline 2']
    >>> glyph.removeComponent(glyph.components[0])
    >>> list(sorted(glyph.identifiers))
    ['component 2', 'contour 2', 'guideline 1', 'guideline 2']
    >>> glyph.removeGuideline(glyph.guidelines[0])
    >>> list(sorted(glyph.identifiers))
    ['component 2', 'contour 2', 'guideline 2']
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
