import weakref
from defcon.tools.notifications import NotificationCenter


class BaseObject(object):

    def __init__(self, dispatcher=None):
        if dispatcher is None:
            dispatcher = NotificationCenter()
        self._dispatcher = dispatcher

    def setParent(self, obj):
        if obj is None:
            self._parent = None
        else:
            self._parent = weakref.ref(obj)

    def getParent(self):
        if self._parent is not None:
            return self._parent()
        return None

    def addObserver(self, observer, methodName, notification):
        self._dispatcher.addObserver(observer=observer, callbackString=methodName,
                                    notification=notification, observable=self)

    def removeObserver(self, observer, notification):
        self._dispatcher.removeObserver(observer=observer, notification=notification, observable=self)

    def _set_dirty(self, value):
        """
        >>> from defcon.test.testTools import NotificationTestObject
        >>> notificationObject = NotificationTestObject()
        >>> obj = BaseObject()
        >>> obj.addObserver(notificationObject, "testCallback", "BaseObject.Changed")
        >>> obj.dirty = True
        BaseObject.Changed True
        >>> obj.dirty
        True
        >>> obj.dirty = False
        BaseObject.Changed False
        """
        self._dirty = value
        notification = "%s.Changed" % self.__class__.__name__
        self._dispatcher.postNotification(notification=notification, observable=self, data=value)

    def _get_dirty(self):
        """
        >>> obj = BaseObject()
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

    def __init__(self, dispatcher=None):
        if dispatcher is None:
            dispatcher = NotificationCenter()
        self._dispatcher = dispatcher


if __name__ == "__main__":
    import doctest
    doctest.testmod()
