import weakref
from defcon.tools.notifications import NotificationCenter
import pickle

class BaseObject(object):

    """
    The base object in defcon from which all other objects should be derived.

    **This object posts the following notifications:**

    ====================
    Name
    ====================
    BaseObject.Changed
    BaseObject.BeginUndo
    BaseObject.EndUndo
    BaseObject.BeginRedo
    BaseObject.EndRedo
    ====================

    Keep in mind that subclasses will not post these same notifications.

    Subclasses must override the following attributes:

    +-------------------------+--------------------------------------------------+
    | Name                    | Notes                                            |
    +=========================+==================================================+
    | changeNotificationName  | This must be a string unique to the class        |
    |                         | indicating the name of the notification          |
    |                         | to be posted when th dirty attribute is set.     |
    +-------------------------+--------------------------------------------------+
    | representationFactories | This must be a dictionary that is shared across  |
    |                         | *all* instances of the class.                    |
    +-------------------------+--------------------------------------------------+
    """

    changeNotificationName = "BaseObject.Changed"
    beginUndoNotificationName = "BaseObject.BeginUndo"
    endUndoNotificationName = "BaseObject.EndUndo"
    beginRedoNotificationName = "BaseObject.BeginRedo"
    endRedoNotificationName = "BaseObject.EndRedo"
    representationFactories = None

    def __init__(self):
        self._init()

    def _init(self):
        self._dispatcher = None
        self._dataOnDisk = None
        self._dataOnDiskTimeStamp = None
        self._undoManager = None
        #self._undoMethods = None
        self._representations = {}

    def __del__(self):
        self.endSelfNotificationObservation()

    # ------
    # Parent
    # ------

    def getParent(self):
        raise NotImplementedError

    # -------------
    # Notifications
    # -------------

    def _get_dispatcher(self):
        if self._dispatcher is not None:
            return self._dispatcher()
        else:
            try:
                dispatcher = self.font.dispatcher
                self._dispatcher = weakref.ref(dispatcher)
            except AttributeError:
                dispatcher = None
        return dispatcher

    dispatcher = property(_get_dispatcher, doc="The :class:`defcon.tools.notifications.NotificationCenter` assigned to the parent of this object.")

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
        dispatcher = self.dispatcher
        if dispatcher is not None:
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
        dispatcher = self.dispatcher
        if dispatcher is not None:
            self.dispatcher.removeObserver(observer=observer, notification=notification, observable=self)

    def hasObserver(self, observer, notification):
        """
        Returns a boolean indicating is the **observer** is registered for **notification**.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.hasObserver(observer=observer,
                notification=notification, observable=anObject)
        """
        dispatcher = self.dispatcher
        if dispatcher is not None:
            return self.dispatcher.hasObserver(observer=observer, notification=notification, observable=self)
        return False

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

    def postNotification(self, notification, data=None):
        """
        Post a **notification** through this object's notification dispatcher.

            * **notification** The name of the notification.
            * **data** Arbitrary data that will be stored in the :class:`Notification` object.

        This is a convenience method that does the same thing as::

            dispatcher = anObject.dispatcher
            dispatcher.postNotification(
                notification=notification, observable=anObject, data=data)
        """
        dispatcher = self.dispatcher
        if dispatcher is not None:
            dispatcher.postNotification(notification=notification, observable=self, data=data)

    # ------------------------
    # Notification Observation
    # ------------------------

    def beginSelfNotificationObservation(self):
        self.addObserver(self, "selfNotificationCallback", notification=None)

    def endSelfNotificationObservation(self):
        self.removeObserver(self, notification=None)
        self._dispatcher = None

    def selfNotificationCallback(self, notification):
        self._destroyRepresentationsForNotification(notification)

    # ----
    # Undo
    # ----

    # manager

    def _get_undoManager(self):
        return self._undoManager

    def setUndoManager(self, manager, prepareUndoFunc="prepareTarget",
        canUndoFunc="canUndo", getUndoTitleFunc="getUndoTitle", undoFunc="undo",
        canRedoFunc="canRedo", getRedoTitleFunc="getRedo", redoFunc="redo"):
        self._undoManager = manager
        self._undoMethods = dict(
            prepareUndo=prepareUndoFunc,
            canUndo=canUndoFunc,
            getUndoTitle=getUndoTitleFunc,
            undo=undoFunc,
            canRedo=canRedoFunc,
            getRedoTitle=getRedoTitleFunc,
            redo=redoFunc,
        )

    undoManager = property(_get_undoManager, doc="The undo manager assigned to this object.")

    # state registration

    def prepareUndo(self, title=None):
        manager = self.undoManager
        prepareUndoFunction = getattr(manager, self._undoMethods["prepareUndo"])
        prepareUndoFunction(title=title)

    # undo

    def canUndo(self):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        canUndoFunction = getattr(manager, self._undoMethods["canUndo"])
        return canUndoFunction()

    def getUndoTitle(self, index=-1):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        getUndoTitleFunction = getattr(
            manager, self._undoMethods["getUndoTitle"])
        return getUndoTitleFunction(index)

    def undo(self, index=-1):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        dispatcher = self._dispatcher
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.beginUndoNotificationName, observable=self)
        undoFunction = getattr(manager, self._undoMethods["undo"])
        undoFunction(index)
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.endUndoNotificationName, observable=self)

    # redo

    def canRedo(self):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        canRedoFunction = getattr(manager, self._undoMethods["canRedo"])
        return canRedoFunction()

    def getRedoTitle(self, index=0):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        getRedoTitleFunction = getattr(
            manager, self._undoMethods["getRedoTitle"])
        return getRedoTitleFunction(index)

    def redo(self, index=0):
        manager = self.undoManager
        if manager is None:
            raise NotImplementedError
        dispatcher = self._dispatcher
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.beginRedoNotificationName, observable=self)
        redoFunction = getattr(manager, self._undoMethods["redo"])
        redoFunction(index)
        if dispatcher is not None:
            self.dispatcher.postNotification(notification=self.endRedoNotificationName, observable=self)

    # ---------------
    # Representations
    # ---------------

    def getRepresentation(self, name, **kwargs):
        """
        Get a representation. **name** must be a registered
        representation name. **\*\*kwargs** will be passed
        to the appropriate representation factory.
        """
        if name not in self._representations:
            self._representations[name] = {}
        representations = self._representations[name]
        subKey = self._makeRepresentationSubKey(**kwargs)
        if subKey not in representations:
            factory = self.representationFactories[name]
            representation = factory["factory"](self, **kwargs)
            representations[subKey] = representation
        return representations[subKey]

    def destroyRepresentation(self, name, **kwargs):
        """
        Destroy the stored representation for **name**
        and **\*\*kwargs**. If no **kwargs** are given,
        any representation with **name** will be destroyed
        regardless of the **kwargs** passed when the
        representation was created.
        """
        if name not in self._representations:
            return
        if not kwargs:
            del self._representations[name]
        else:
            representations = self._representations[name]
            subKey = self._makeRepresentationSubKey(**kwargs)
            if subKey in representations:
                del self._representations[name][subKey]

    def destroyAllRepresentations(self, notification=None):
        """
        Destroy all representations.
        """
        self._representations.clear()

    def _destroyRepresentationsForNotification(self, notification):
        notificationName = notification.name
        for name, dataDict in list(self.representationFactories.items()):
            if notificationName in dataDict["destructiveNotifications"]:
                self.destroyRepresentation(name)

    def representationKeys(self):
        """
        Get a list of all representation keys that are
        currently cached.
        """
        representations = []
        for name, subDict in list(self._representations.items()):
            for subKey in list(subDict.keys()):
                kwargs = {}
                if subKey is not None:
                    for k, v in subKey:
                        kwargs[k] = v
                representations.append((name, kwargs))
        return representations

    def hasCachedRepresentation(self, name, **kwargs):
        """
        Returns a boolean indicating if a representation for
        **name** and **\*\*kwargs** is cached in the object.
        """
        if name not in self._representations:
            return False
        subKey = self._makeRepresentationSubKey(**kwargs)
        return subKey in self._representations[name]

    def _makeRepresentationSubKey(self, **kwargs):
        if kwargs:
            key = sorted(kwargs.items())
            key = tuple(key)
        else:
            key = None
        return key

    # -----
    # Dirty
    # -----

    def _set_dirty(self, value):
        self._dirty = value
        dispatcher = self.dispatcher
        if dispatcher is not None:
            self.postNotification(self.changeNotificationName)

    def _get_dirty(self):
        return self._dirty

    dirty = property(_get_dirty, _set_dirty, doc="The dirty state of the object. True if the object has been changed. False if not. Setting this to True will cause the base changed notification to be posted. The object will automatically maintain this attribute and update it as you change the object.")

    # -----------------------------
    # Serialization/Deserialization
    # -----------------------------

    def serialize(self, dumpFunc=None, whitelist=None, blacklist=None):
        data = self.getDataForSerialization(whitelist=whitelist, blacklist=blacklist)

        dump = dumpFunc if dumpFunc is not None else pickle.dumps
        return dump(data)

    def deserialize(self, data, loadFunc=None):
        load = loadFunc if loadFunc is not None else pickle.loads
        self.setDataFromSerialization(load(data))

    def getDataForSerialization(self, **kwargs):
        """
        Return a dict of data that can be pickled.
        """
        return {}

    def setDataFromSerialization(self, data):
        """
        Restore state from the provided data-dict.
        """
        pass

    def _serialize(self, getters, whitelist=None, blacklist=None, **kwargs):
        """ A helper function for the defcon objects.

        Return a dict where the keys are the keys in getters and the values
        are the results of the getter functions

        getters is a list of tuples:
        [
            (:str:key, :callable:getter_function)
        ]

        if a whitelist is not None: the key must be in whitelist
        if a blacklist is not None: the key must not be in blacklist
        """
        data = {}
        for key, getter in getters:
            if whitelist is not None and key not in whitelist:
                continue
            if blacklist is not None and key in blacklist:
                continue
            data[key] = getter(key)
        return data




class BaseDictObject(dict, BaseObject):

    """
    A subclass of BaseObject that implements a dict API. Any changes
    to the contents of the object will cause the dirty attribute
    to be set to True.
    """

    setItemNotificationName = None
    deleteItemNotificationName = None
    clearNotificationName = None
    updateNotificationName = None

    def __init__(self):
        super(BaseDictObject, self).__init__()
        self._init()
        self._dirty = False

    def _get_dict(self):
        from warnings import warn
        warn(
            "BaseDictObject is now a dict and _dict is gone.",
            DeprecationWarning
        )
        return self

    _dict = property(_get_dict)

    def __hash__(self):
        return id(self)

    def __setitem__(self, key, value):
        oldValue = None
        if key in self:
            oldValue = self[key]
            if value is not None and oldValue == value:
                # don't do this if the value is None since some
                # subclasses establish their keys at startup with
                # self[key] = None
                return
        super(BaseDictObject, self).__setitem__(key, value)
        if self.setItemNotificationName is not None:
            self.postNotification(self.setItemNotificationName, data=dict(key=key, oldValue=oldValue, newValue=value))
        self.dirty = True

    def __delitem__(self, key):
        super(BaseDictObject, self).__delitem__(key)
        if self.deleteItemNotificationName is not None:
            self.postNotification(self.deleteItemNotificationName, data=dict(key=key))
        self.dirty = True

    def __deepcopy__(self, memo={}):
        import copy
        obj = self.__class__()
        for k, v in list(self.items()):
            k = copy.deepcopy(k)
            v = copy.deepcopy(v)
            obj[k] = v
        return obj

    def clear(self):
        if not len(self):
            return
        super(BaseDictObject, self).clear()
        if self.clearNotificationName is not None:
            self.postNotification(self.clearNotificationName)
        self.dirty = True

    def update(self, other):
        super(BaseDictObject, self).update(other)
        if self.updateNotificationName is not None:
            self.postNotification(self.updateNotificationName)
        self.dirty = True

    # -----------------------------
    # Serialization/Deserialization
    # -----------------------------

    def getDataForSerialization(self, **kwargs):
        from copy import deepcopy

        deep_get = lambda k: deepcopy(self[k])

        getters = []
        for k in list(self.keys()):
            k = deepcopy(k) # needed?
            getters.append((k, deep_get))

        return self._serialize(getters, **kwargs)

    def setDataFromSerialization(self, data):
        self.clear()
        self.update(data)

def _representationTestFactory(obj, **kwargs):
    return repr(tuple(sorted(kwargs.items())))

def _testRepresentations():
    """
    >>> obj = BaseObject()
    >>> obj.representationFactories = dict(test=dict(factory=_representationTestFactory, destructiveNotifications=["BaseObject.Changed"]))

    >>> obj.getRepresentation("test")
    '()'
    >>> obj.getRepresentation("test", attr1="foo", attr2="bar", attr3=1)
    "(('attr1', 'foo'), ('attr2', 'bar'), ('attr3', 1))"
    >>> obj.representationKeys()
    [('test', {}), ('test', {'attr2': 'bar', 'attr3': 1, 'attr1': 'foo'})]
    >>> obj.hasCachedRepresentation("test")
    True
    >>> obj.hasCachedRepresentation("test", attr1="foo", attr2="bar", attr3=1)
    True
    >>> obj.hasCachedRepresentation("test", attr1="not foo", attr2="bar", attr3=1)
    False

    >>> obj.destroyAllRepresentations()
    >>> obj.representationKeys()
    []

    >>> obj.representationFactories["foo"] =  dict(factory=_representationTestFactory, destructiveNotifications=["BaseObject.Changed"])
    >>> obj.getRepresentation("test")
    '()'
    >>> obj.getRepresentation("test", attr1="foo", attr2="bar", attr3=1)
    "(('attr1', 'foo'), ('attr2', 'bar'), ('attr3', 1))"
    >>> obj.getRepresentation("test", attr21="foo", attr22="bar", attr23=1)
    "(('attr21', 'foo'), ('attr22', 'bar'), ('attr23', 1))"
    >>> obj.getRepresentation("foo")
    '()'
    >>> obj.destroyRepresentation("test", attr21="foo", attr22="bar", attr23=1)
    >>> obj.representationKeys()
    [('test', {}), ('test', {'attr2': 'bar', 'attr3': 1, 'attr1': 'foo'}), ('foo', {})]
    >>> obj.destroyRepresentation("test")
    >>> obj.representationKeys()
    [('foo', {})]
    """

#def _testDirty():
#    """
#    # set
#    >>> from defcon.test.testTools import NotificationTestObject
#    >>> notificationObject = NotificationTestObject()
#    >>> obj = BaseObject()
#    >>> obj.dispatcher = NotificationCenter()
#    >>> obj.addObserver(notificationObject, "testCallback", "BaseObject.Changed")
#    >>> obj.dirty = True
#    BaseObject.Changed None
#    >>> obj.dirty
#    True
#    >>> obj.dirty = False
#    BaseObject.Changed None
#
#    # get
#    >>> obj = BaseObject()
#    >>> obj._dispatcher = NotificationCenter()
#    >>> obj.dirty = True
#    >>> obj.dirty
#    True
#    >>> obj.dirty = False
#    >>> obj.dirty
#    False
#
#    # set
#    >>> obj = BaseDictObject()
#    >>> obj._dispatcher = NotificationCenter()
#    >>> obj.addObserver(notificationObject, "testCallback", "BaseObject.Changed")
#    >>> obj.dirty = True
#    BaseObject.Changed None
#    >>> obj.dirty
#    True
#    >>> obj.dirty = False
#    BaseObject.Changed None
#
#    # get
#    >>> obj = BaseDictObject()
#    >>> obj._dispatcher = NotificationCenter()
#    >>> obj.dirty = True
#    >>> obj.dirty
#    True
#    >>> obj.dirty = False
#    >>> obj.dirty
#    False
#    """

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
