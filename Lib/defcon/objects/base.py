import weakref
from defcon.tools.notifications import NotificationCenter


class BaseObject(object):

    _notificationName = "BaseObject.Changed"

    def __init__(self):
        self._dispatcher = None
        self._dataOnDisk = None
        self._dataOnDiskTimeStamp = None

    def setParent(self, obj):
        if obj is None:
            self._parent = None
        else:
            self._parent = weakref.ref(obj)

    def getParent(self):
        if self._parent is not None:
            return self._parent()
        return None

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

    dispatcher = property(_get_dispatcher, _set_dispatcher)

    def addObserver(self, observer, methodName, notification):
        self.dispatcher.addObserver(observer=observer, callbackString=methodName,
                                    notification=notification, observable=self)

    def removeObserver(self, observer, notification):
        self.dispatcher.removeObserver(observer=observer, notification=notification, observable=self)

    def _set_dirty(self, value):
        """
        >>> from defcon.test.testTools import NotificationTestObject
        >>> notificationObject = NotificationTestObject()
        >>> obj = BaseObject()
        >>> obj._dispatcher = NotificationCenter()
        >>> obj.addObserver(notificationObject, "testCallback", "BaseObject.Changed")
        >>> obj.dirty = True
        BaseObject.Changed True
        >>> obj.dirty
        True
        >>> obj.dirty = False
        BaseObject.Changed False
        """
        self._dirty = value
        if self._dispatcher is not None:
            self.dispatcher.postNotification(notification=self._notificationName, observable=self, data=value)

    def _get_dirty(self):
        """
        >>> obj = BaseObject()
        >>> obj._dispatcher = NotificationCenter()
        >>> obj.dirty = True
        >>> obj.dirty
        True
        >>> obj.dirty = False
        >>> obj.dirty
        False
        """
        return self._dirty

    dirty = property(_get_dirty, _set_dirty)


class BaseDictObject(dict, BaseObject):
    pass


if __name__ == "__main__":
    import doctest
    doctest.testmod()
