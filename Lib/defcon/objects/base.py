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
        BaseObject.Changed None
        >>> obj.dirty
        True
        >>> obj.dirty = False
        BaseObject.Changed None
        """
        self._dirty = value
        if self._dispatcher is not None:
            self.dispatcher.postNotification(notification=self._notificationName, observable=self)

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


class BaseDictObject(BaseObject):

    def __init__(self):
        super(BaseDictObject, self).__init__()
        self._dict = {}
        self._dirty = False

    def __contains__(self, key):
        """
        >>> obj = BaseDictObject()
        >>> obj["A"] = 1
        >>> "A" in obj
        True
        >>> "B" in obj
        False
        """
        return key in self._dict

    has_key = __contains__

    def __len__(self):
        """
        >>> obj = BaseDictObject()
        >>> len(obj)
        0
        >>> obj["A"] = 1
        >>> len(obj)
        1
        """
        return len(self._dict)

    def __getitem__(self, key):
        """
        >>> obj = BaseDictObject()
        >>> obj["A"] = 1
        >>> obj["A"]
        1
        """
        return self._dict[key]

    def __setitem__(self, key, value):
        """
        >>> obj = BaseDictObject()
        >>> obj["A"] = 1
        >>> obj["A"]
        1
        >>> obj.dirty
        True
        """
        self._dict[key] = value
        self.dirty = True

    def __delitem__(self, key):
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
        del self._dict[key]
        self.dirty = True

    def get(self, key, default=None):
        """
        >>> obj = BaseDictObject()
        >>> obj["A"] = 1
        >>> obj.get("A")
        1
        >>> obj.get("B")
        """
        return self._dict.get(key, default)

    def clear(self):
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
        self._dict.clear()
        self.dirty = True

    def update(self, other):
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
        self._dict.update(other)
        self.dirty = True

    def keys(self):
        """
        >>> obj = BaseDictObject()
        >>> obj["A"] = 1
        >>> obj.keys()
        ['A']
        """
        return self._dict.keys()

    def values(self):
        """
        >>> obj = BaseDictObject()
        >>> obj["A"] = 1
        >>> obj.values()
        [1]
        """
        return self._dict.values()

    def items(self):
        """
        >>> obj = BaseDictObject()
        >>> obj["A"] = 1
        >>> obj.items()
        [('A', 1)]
        """
        return self._dict.items()


if __name__ == "__main__":
    import doctest
    doctest.testmod()
