import weakref
from defcon.tools.notifications import NotificationCenter


class BaseObject(object):

    """
    The base object in defcon from which all other objects should be derived.

    **This object posts the following notifications:**

    ====================  ====
    Name                  Note
    ====================  ====
    BaseObject.Changed    Posted when the *dirty* attribute is set.
    BaseObject.BeginUndo  Posted when an undo begins.
    BaseObject.EndUndo    Posted when an undo ends.
    BaseObject.BeginRedo  Posted when a redo begins.
    BaseObject.EndRedo    Posted when a redo ends.
    ====================  ====

    Keep in mind that subclasses will not post these same notifications.
    """

    changeNotificationName = "BaseObject.Changed"
    beginUndoNotificationName = "BaseObject.BeginUndo"
    endUndoNotificationName = "BaseObject.EndUndo"
    beginRedoNotificationName = "BaseObject.BeginRedo"
    endRedoNotificationName = "BaseObject.EndRedo"

    def __init__(self):
        self._parent = None
        self._dispatcher = None
        self._dataOnDisk = None
        self._dataOnDiskTimeStamp = None
        self._undoManager = None
        # handle the old _notificationName attribute
        if hasattr(self, "_notificationName"):
            from warnings import warn
            warn(
                "_notificationName has been deprecated. Use changeNotificationName instead.",
                DeprecationWarning
            )
            self.changeNotificationName = self._notificationName
        self._notificationName = self.changeNotificationName

    # ------
    # Parent
    # ------

    def setParent(self, obj):
        """
        Set the parent of the object. This will reference the parent using weakref.
        """
        if obj is None:
            self._parent = None
        else:
            self._parent = weakref.ref(obj)

    def getParent(self):
        """
        Get the parent. Returns None if no parent is set.
        Note that because the reference to the parent is stored
        as a weakref, the parent can disappear if it is no longer
        referenced by any object other than this one.
        """
        if self._parent is not None:
            return self._parent()
        return None

    # -------------
    # Notifications
    # -------------

    def _get_dispatcher(self):
        if self._dispatcher is None:
            return None
        elif isinstance(self._dispatcher, NotificationCenter):
            return self._dispatcher
        else:
            return self._dispatcher()

    def _set_dispatcher(self, dispatcher):
        if dispatcher is None:
            pass
        elif isinstance(dispatcher, NotificationCenter):
            self._dispatcher = weakref.ref(dispatcher)
        else:
            self._dispatcher = dispatcher

    dispatcher = property(_get_dispatcher, _set_dispatcher, doc="The :class:`defcon.tools.notifications.NotificationCenter` assigned to this object.")

    def addObserver(self, observer, methodName, notification):
        """
        Add an observer to this object's notification dispatcher.

        * **observer** An object that can be referenced with weakref.
        * **methodName** A string epresenting the method to be called
          when the notification is posted.
        * **notification** The notification that the observer should
          be notified of.

        The method that will be called as a result of the action
        must accept a single *notification* argument. This will
        be a :class:`defcon.tools.notifications.Notification` object.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.addObserver(observer=observer, methodName=methodName,
                notification=notification, observable=anObject)
        """
        self.dispatcher.addObserver(observer=observer, methodName=methodName,
                                    notification=notification, observable=self)

    def removeObserver(self, observer, notification):
        """
        Remove an observer from this object's notification dispatcher.

        * **observer** A registered object.
        * **notification** The notification that the observer was registered
          to be notified of.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.removeObserver(observer=observer,
                notification=notification, observable=anObject)
        """
        self.dispatcher.removeObserver(observer=observer, notification=notification, observable=self)

    def hasObserver(self, observer, notification):
        """
        Returns a boolean indicating is the **observer** is registered for **notification**.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.hasObserver(observer=observer,
                notification=notification, observable=anObject)
        """
        return self.dispatcher.hasObserver(observer=observer, notification=notification, observable=self)

    def holdNotifications(self, notification=None):
        """
        Hold this object's notifications until told to release them.

        * **notification** The specific notification to hold. This is optional.
          If no *notification* is given, all notifications will be held.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.holdNotifications(
                observable=anObject, notification=notification)
        """
        dispatcher = self.dispatcher
        if dispatcher is not None:
            dispatcher.holdNotifications(observable=self, notification=notification)

    def releaseHeldNotifications(self, notification=None):
        """
        Release this object's held notifications.

        * **notification** The specific notification to hold. This is optional.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.releaseHeldNotifications(
                observable=anObject, notification=notification)
        """
        dispatcher = self.dispatcher
        if dispatcher is not None:
            dispatcher.releaseHeldNotifications(observable=self, notification=notification)

    def disableNotifications(self, notification=None, observer=None):
        """
        Disable this object's notifications until told to resume them.

        * **notification** The specific notification to disable. This is optional.
          If no *notification* is given, all notifications will be disabled.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.disableNotifications(
                observable=anObject, notification=notification, observer=observer)
        """
        dispatcher = self.dispatcher
        if dispatcher is not None:
            dispatcher.disableNotifications(observable=self, notification=notification, observer=observer)

    def enableNotifications(self, notification=None, observer=None):
        """
        Enable this object's notifications.

        * **notification** The specific notification to enable. This is optional.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.enableNotifications(
                observable=anObject, notification=notification, observer=observer)
        """
        dispatcher = self.dispatcher
        if dispatcher is not None:
            dispatcher.enableNotifications(observable=self, notification=notification, observer=observer)

    # -----
    # Dirty
    # -----

    def _set_dirty(self, value):
        self._dirty = value
        if self._dispatcher is not None:
            self.dispatcher.postNotification(notification=self.changeNotificationName, observable=self)

    def _get_dirty(self):
        return self._dirty

    dirty = property(_get_dirty, _set_dirty, doc="The dirty state of the object. True if the object has been changed. False if not. Setting this to True will cause the base changed notification to be posted. The object will automatically maintain this attribute and update it as you change the object.")

    # ----
    # Undo
    # ----

    # manager

    def _get_undoManager(self):
        return self._undoManager

    def _set_undoManager(self, manager):
        self._undoManager = manager
        manager.setObject(self)

    undoManager = property(_get_undoManager, _set_undoManager, doc="The undo manager assigned to this object.")

    # state registration

    def prepareUndo(self, title=None):
        self.undoManager.prepareTarget(title=title)

    # undo

    def canUndo(self):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        return manager.canUndo()

    def getUndoTitle(self, index=-1):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        return manager.getUndoTitle(index)

    def getUndoTitles(self):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        return manager.getUndoTitles()

    def undo(self, index=-1):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        dispatcher = self._dispatcher
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.beginUndoNotificationName, observable=self)
        manager.undo(index)
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.endUndoNotificationName, observable=self)

    # redo

    def canRedo(self):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        return manager.canRedo()

    def getRedoTitle(self, index=0):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        return manager.getRedoTitle(index)

    def getRedoTitles(self):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        return manager.getRedoTitles()

    def redo(self, index=0):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        dispatcher = self._dispatcher
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.beginRedoNotificationName, observable=self)
        manager.undo(index)
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.endRedoNotificationName, observable=self)

    # serialization

    def serializeForUndo(self, pack=True):
        from pickle import dumps
        import zlib
        # make the data dict
        data = dict(
            serializedData=self.getDataToSerializeForUndo(),
            customData=self.getCustomDataToSerializeForUndo()
        )
        if pack:
            # pickle
            data = dumps(data, 0)
            # compress
            data = zlib.compress(data, 9)
        return dict(packed=pack, data=data)

    def getDataToSerializeForUndo(self):
        raise NotImplementedError

    def getCustomDataToSerializeForUndo(self):
        return None

    # deserealization

    def deserializeFromUndo(self, data):
        from pickle import loads
        import zlib
        packed = data["packed"]
        data = data["data"]
        if packed:
            # decompress
            data = zlib.decompress(data)
            # unpickle
            data = loads(data)
        # hold notifications
        self.holdNotifications()
        # deserialize basic data
        self.loadDeserializedDataFromUndo(data["serializedData"])
        # deserialize custom data
        self.loadDeserializedCustomDataFromUndo(data["customData"])
        # release held notifications
        self.releaseHeldNotifications()

    def loadDeserializedDataFromUndo(self, data):
        raise NotImplementedError

    def loadDeserializedCustomDataFromUndo(self, data):
        pass


class BaseDictObject(BaseObject):

    """
    A subclass of BaseObject that implements a dict API. Any changes
    to the contents of the object will cause the dirty attribute
    to be set to True.
    """

    def __init__(self):
        super(BaseDictObject, self).__init__()
        self._dict = {}
        self._dirty = False

    def __contains__(self, key):
        return key in self._dict

    has_key = __contains__

    def __len__(self):
        return len(self._dict)

    def __getitem__(self, key):
        return self._dict[key]

    def __setitem__(self, key, value):
        self._dict[key] = value
        self.dirty = True

    def __delitem__(self, key):
        del self._dict[key]
        self.dirty = True

    def __copy__(self):
        import copy
        obj = self.__class__()
        obj.update(copy.copy(self._dict))
        return obj

    def __deepcopy__(self, memo={}):
        import copy
        obj = self.__class__()
        obj.update(copy.deepcopy(self._dict, memo))
        return obj

    def get(self, key, default=None):
        return self._dict.get(key, default)

    def clear(self):
        self._dict.clear()
        self.dirty = True

    def update(self, other):
        self._dict.update(other)
        self.dirty = True

    def keys(self):
        return list(self._dict.keys())

    def values(self):
        return list(self._dict.values())

    def items(self):
        return list(self._dict.items())

    # ----
    # Undo
    # ----

    def getDataToSerializeForUndo(self):
        return self._dict

    def loadDeserializedDataFromUndo(self, data):
        self.update(data)


def _testDirty():
    """
    # set
    >>> from defcon.test.testTools import NotificationTestObject
    >>> notificationObject = NotificationTestObject()
    >>> obj = BaseObject()
    >>> obj._dispatcher = NotificationCenter()
    >>> obj.addObserver(notificationObject, "testCallback", "BaseObject.Changed")
    >>> obj.dirty = True
    BaseObject.Changed None
    >>> obj.dirty
    True
    >>> obj.dirty = False
    BaseObject.Changed None

    # get
    >>> obj = BaseObject()
    >>> obj._dispatcher = NotificationCenter()
    >>> obj.dirty = True
    >>> obj.dirty
    True
    >>> obj.dirty = False
    >>> obj.dirty
    False
    """

def _testContains():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> "A" in obj
    True
    >>> "B" in obj
    False
    """

def _testLen():
    """
    >>> obj = BaseDictObject()
    >>> len(obj)
    0
    >>> obj["A"] = 1
    >>> len(obj)
    1
    """

def _testGetitem():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj["A"]
    1
    """

def _testSetitem():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj["A"]
    1
    >>> obj.dirty
    True
    """

def _testDelitem():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj.dirty = False
    >>> del obj["A"]
    >>> "A" in obj
    False
    >>> obj.dirty
    True
    """

def _testGet():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj.get("A")
    1
    >>> obj.get("B")
    """

def _testClear():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj.dirty = False
    >>> obj.clear()
    >>> len(obj)
    0
    >>> obj.dirty
    True
    """

def _testUpdate():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj.dirty = False
    >>> obj.update(dict(A=2, B=3))
    >>> len(obj)
    2
    >>> obj["A"]
    2
    >>> obj["B"]
    3
    >>> obj.dirty
    True
    """

def _testKeys():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj.keys()
    ['A']
    """

def _testValues():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj.values()
    [1]
    """

def _testItems():
    """
    >>> obj = BaseDictObject()
    >>> obj["A"] = 1
    >>> obj.items()
    [('A', 1)]
    """


if __name__ == "__main__":
    import doctest
    doctest.testmod()
