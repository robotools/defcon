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
    ====================  ====

    Keep in mind that subclasses will not post these same notifications.
    """

    changeNotificationName = "BaseObject.Changed"

    def __init__(self):
        self._init()

    def _init(self):
        self._parent = None
        self._dispatcher = None
        self._dataOnDisk = None
        self._dataOnDiskTimeStamp = None
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


class BaseDictObject(dict, BaseObject):

    """
    A subclass of BaseObject that implements a dict API. Any changes
    to the contents of the object will cause the dirty attribute
    to be set to True.
    """

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
        if self.get(key) == value:
            return
        super(BaseDictObject, self).__setitem__(key, value)
        self.dirty = True

    def __delitem__(self, key):
        super(BaseDictObject, self).__delitem__(key)
        self.dirty = True

    def __copy__(self):
        import copy
        obj = self.__class__()
        obj.update(copy.copy(self))
        return obj

    def __deepcopy__(self, memo={}):
        import copy
        obj = self.__class__()
        obj.update(copy.deepcopy(self, memo))
        return obj

    def clear(self):
        if not len(self):
            return
        super(BaseDictObject, self).clear()
        self.dirty = True

    def update(self, other):
        super(BaseDictObject, self).update(other)
        self.dirty = True


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

    # set
    >>> obj = BaseDictObject()
    >>> obj._dispatcher = NotificationCenter()
    >>> obj.addObserver(notificationObject, "testCallback", "BaseObject.Changed")
    >>> obj.dirty = True
    BaseObject.Changed None
    >>> obj.dirty
    True
    >>> obj.dirty = False
    BaseObject.Changed None

    # get
    >>> obj = BaseDictObject()
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
