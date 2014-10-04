"""
A flexible and relatively robust implementation
of the Observer Pattern.
"""

import weakref

"""

----------------------
Internal Documentation
----------------------

Storage Structures:

registry : {
        (notification, observable) : ObserverDict(
            observer : method name
        )
    }

holds : {
    (notification, observable, observer) : {
        count=int,
        notifications=[
            (notification name, observable ref, data)
        ]
    )
}

disabled : {
    (notification, observable, observer) : count
}

"""


class NotificationCenter(object):

    def __init__(self):
        self._registry = {}
        self._holds = {}
        self._disabled = {}

    # -----
    # Basic
    # -----

    def addObserver(self, observer, methodName, notification=None, observable=None):
        """
        Add an observer to this notification dispatcher.

        * **observer** An object that can be referenced with weakref.
        * **methodName** A string epresenting the method to be called
          when the notification is posted.
        * **notification** The notification that the observer should
          be notified of. If this is None, all notifications for
          the *observable* will be posted to *observer*.
        * **observable** The object to observe. If this is None,
          all notifications with the name provided as *notification*
          will be posted to the *observer*.

        If None is given for both *notification* and *observable*
        **all** notifications posted will be sent to the method
        given method of the observer.

        The method that will be called as a result of the action
        must accept a single *notification* argument. This will
        be a :class:`Notification` object.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        observer = weakref.ref(observer)
        key = (notification, observable)
        if key not in self._registry:
            self._registry[key] = ObserverDict()
        assert observer not in self._registry[key], "An observer is only allowed to have one callback for a given notification + observable combination."
        self._registry[key][observer] = methodName

    def hasObserver(self, observer, notification, observable):
        """
        Returns a boolean indicating if the **observer** is registered
        for **notification** posted by **observable**. Either
        *observable* or *notification* may be None.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        key = (notification, observable)
        if key not in self._registry:
            return False
        observer = weakref.ref(observer)
        return observer in self._registry[key]

    def removeObserver(self, observer, notification, observable):
        """
        Remove an observer from this notification dispatcher.

        * **observer** A registered object.
        * **notification** The notification that the observer was registered
          to be notified of.
        * **observable** The object being observed.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        key = (notification, observable)
        if key not in self._registry:
            return
        observer = weakref.ref(observer)
        if observer in self._registry[key]:
            del self._registry[key][observer]
        if not len(self._registry[key]):
            del self._registry[key]

    def postNotification(self, notification, observable, data=None):
        assert notification is not None
        assert observable is not None
        observableRef = weakref.ref(observable)
        # observer independent hold/disabled
        # ----------------------------------
        if self._holds or self._disabled:
            holdDisabledPossibilities = (
                # least specific -> most specific
                # suspended for all
                (None, None, None),
                # suspended for this notification
                (notification, None, None),
                # suspended for this observer
                (None, observableRef, None),
                # suspended for this notification + observable
                (notification, observableRef, None)
            )
            for key in holdDisabledPossibilities:
                if key in self._disabled:
                    return
                if key in self._holds:
                    n = (notification, observableRef, data)
                    if not self._holds[key]["notifications"] or self._holds[key]["notifications"][-1] != n:
                        self._holds[key]["notifications"].append(n)
                    return
        # posting
        # -------
        notificationObj = Notification(notification, observableRef, data)
        registryPossibilities = (
            # most specific -> least specific
            (notification, observableRef),
            (notification, None),
            (None, observableRef),
            (None, None)
        )
        for key in registryPossibilities:
            if key not in self._registry:
                continue
            for observerRef, methodName in list(self._registry[key].items()):
                # observer specific hold/disabled
                # -------------------------------
                if self._holds or self._disabled:
                    holdDisabledPossibilities = (
                        # least specific -> most specific
                        # suspended for observer
                        (None, None, observerRef),
                        # suspended for notification + observer
                        (notification, None, observerRef),
                        # suspended for observable + observer
                        (None, observableRef, observerRef),
                        # suspended for notification + observable + observer
                        (notification, observableRef, observerRef)
                    )
                    disabled = False
                    if self._disabled:
                        for disableKey in holdDisabledPossibilities:
                            if disableKey in self._disabled:
                                disabled = True
                                break
                    if disabled:
                        continue
                    hold = False
                    if self._holds:
                        for holdKey in holdDisabledPossibilities:
                            if holdKey in self._holds:
                                hold = True
                                n = (notification, observableRef, data)
                                if not self._holds[holdKey]["notifications"] or self._holds[holdKey]["notifications"][-1] != n:
                                    self._holds[holdKey]["notifications"].append(n)
                                break
                    if hold:
                        continue
                # post
                # ----
                observer = observerRef()
                if observer is None:
                    # dead ref.
                    # XXX: delete?
                    continue
                callback = getattr(observer, methodName)
                callback(notificationObj)

    # ----
    # Hold
    # ----

    def holdNotifications(self, observable=None, notification=None, observer=None):
        """
        Hold all notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to. This is optional.
          If no *observable* is given, *all* *notifications* will be held.
        * **notification** The name of the notification. This is optional.
          If no *notification* is given, *all* notifications for *observable*
          will be held.
         * **observer** The specific observer to not hold notifications for.
           If no *observer* is given, the appropriate notifications will be
           held for all observers.

        Held notifications will be posted after the matching *notification*
        and *observable* have been passed to :meth:`Notification.releaseHeldNotifications`.
        This object will retain a count of how many times it has been told to
        hold notifications for *notification* and *observable*. It will not
        post the notifications until the *notification* and *observable*
        have been released the same number of times.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = (notification, observable, observer)
        if key not in self._holds:
            self._holds[key] = dict(count=0, notifications=[])
        self._holds[key]["count"] += 1

    def releaseHeldNotifications(self, observable=None, notification=None, observer=None):
        """
        Release all held notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to. This is optional.
        * **notification** The name of the notification. This is optional.
        * **observer** The observer. This is optional.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = (notification, observable, observer)
        self._holds[key]["count"] -= 1
        if self._holds[key]["count"] == 0:
            notifications = self._holds[key]["notifications"]
            del self._holds[key]
            for notification, observableRef, data in notifications:
                self.postNotification(notification, observableRef(), data)

    def areNotificationsHeld(self, observable=None, notification=None, observer=None):
        """
        Returns a boolean indicating if notifications posted to all objects observing
        **notification** in **observable** are being held.

        * **observable** The object that the notification belongs to. This is optional.
        * **notification** The name of the notification. This is optional.
        * **observer** The observer. This is optional.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = (notification, observable, observer)
        return key in self._holds

    # -------
    # Disable
    # -------

    def disableNotifications(self, observable=None, notification=None, observer=None):
        """
        Disable all posts of **notification** from **observable** posted
        to **observer** observing.

        * **observable** The object that the notification belongs to. This is optional.
          If no *observable* is given, *all* *notifications* will be disabled for *observer*.
        * **notification** The name of the notification. This is optional.
          If no *notification* is given, *all* notifications for *observable*
          will be disabled for *observer*.
        * **observer** The specific observer to not send posts to. If no
          *observer* is given, the appropriate notifications will not
          be posted to any observers.

        This object will retain a count of how many times it has been told to
        disable notifications for *notification* and *observable*. It will not
        enable new notifications until the *notification* and *observable*
        have been released the same number of times.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = (notification, observable, observer)
        if key not in self._disabled:
            self._disabled[key] = 0
        self._disabled[key] += 1

    def enableNotifications(self, observable=None, notification=None, observer=None):
        """
        Enable notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to. This is optional.
        * **notification** The name of the notification. This is optional.
        * **observer** The observer. This is optional.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = (notification, observable, observer)
        self._disabled[key] -= 1
        if self._disabled[key] == 0:
            del self._disabled[key]

    def areNotificationsDisabled(self, observable=None, notification=None, observer=None):
        """
        Returns a boolean indicating if notifications posted to all objects observing
        **notification** in **observable** are disabled.

        * **observable** The object that the notification belongs to. This is optional.
        * **notification** The name of the notification. This is optional.
        * **observer** The observer. This is optional.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = (notification, observable, observer)
        return key in self._disabled


class Notification(object):

    """An object that wraps notification data."""

    __slots__ = ("_name", "_objRef", "_data")

    def __init__(self, name, objRef, data):
        self._name = name
        self._objRef = objRef
        self._data = data

    def __repr__(self):
        return "<Notification: %s %s>" % (self.name, repr(self.object))

    def _get_name(self):
        return self._name

    name = property(_get_name, doc="The notification name. A string.")

    def _get_object(self):
        if self._objRef is not None:
            return self._objRef()
        return None

    object = property(_get_object, doc="The observable object the notification belongs to.")

    def _get_data(self):
        return self._data

    data = property(_get_data, doc="Arbitrary data passed along with the notification. There is no set format for this data and there is not requirement that any data be present. Refer to the documentation for methods that are responsible for generating notifications for information about this data.")


class ObserverDict(dict):

    """An object for storing ordered observers."""

    def __init__(self):
        super(ObserverDict, self).__init__()
        self._order = []

    def keys(self):
        return list(self._order)

    def values(self):
        return [self[key] for key in self]

    def items(self):
        return [(key, self[key]) for key in self]

    def __iter__(self):
        order = self._order
        while order:
            yield order[0]
            order = order[1:]

    def iterkeys(self):
        return iter(self)

    def itervalues(self):
        for key in self:
            yield self[key]

    def iteritems(self):
        for key in self:
            yield (key, self[key])

    def __delitem__(self, key):
        super(ObserverDict, self).__delitem__(key)
        self._order.remove(key)

    def __setitem__(self, key, value):
        if key in self:
            del self[key]
        super(ObserverDict, self).__setitem__(key, value)
        self._order.append(key)

# -----
# Tests
# -----

class _TestObserver(object):

    def notificationCallback(self, notification):
        print(notification.name, notification.object.name)


class _TestObservable(object):

    def __init__(self, center, name):
        self.center = center
        self.name = name

    def postNotification(self, name):
        self.center.postNotification(name, self)


def _testAddObserver():
    """
    # notification, observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable)
    >>> center.hasObserver(observer, "A", observable)
    True
    >>> center.hasObserver(observer, "B", observable)
    False

    # notification, no observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", None)
    >>> center.hasObserver(observer, "A", None)
    True
    >>> center.hasObserver(observer, "A", observable)
    False

    # no notification, observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", None, observable)
    >>> center.hasObserver(observer, None, observable)
    True
    >>> center.hasObserver(observer, "A", observable)
    False

    # no notification, no observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", None, None)
    >>> center.hasObserver(observer, None, None)
    True
    >>> center.hasObserver(observer, "A", observable)
    False
    >>> center.hasObserver(observer, None, observable)
    False
    >>> center.hasObserver(observer, "A", None)
    False
    """

def _testRemoveObserver():
    """
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable)
    >>> center.removeObserver(observer, "A", observable)
    >>> center.hasObserver(observer, "A", observable)
    False

    # notification, observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable)
    >>> center.removeObserver(observer, "A", observable)
    >>> center.hasObserver(observer, "A", observable)
    False

    # notification, no observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", None)
    >>> center.removeObserver(observer, "A", None)
    >>> center.hasObserver(observer, "A", None)
    False

    # no notification, observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", None, observable)
    >>> center.removeObserver(observer, None, observable)
    >>> center.hasObserver(observer, None, observable)
    False

    # no notification, no observable
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", None, None)
    >>> center.removeObserver(observer, None, None)
    >>> center.hasObserver(observer, None, None)
    False
    """

def _testPostNotification():
    """
    # notification, observable
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.postNotification("A", observable1)
    A Observable1
    >>> center.postNotification("A", observable2)
    >>> center.postNotification("B", observable1)
    >>> center.postNotification("B", observable2)

    # notification, no observable
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", None)
    >>> center.postNotification("A", observable1)
    A Observable1
    >>> center.postNotification("A", observable2)
    A Observable2
    >>> center.postNotification("B", observable1)
    >>> center.postNotification("B", observable2)

    # no notification, observable
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", None, observable1)
    >>> center.postNotification("A", observable1)
    A Observable1
    >>> center.postNotification("A", observable2)
    >>> center.postNotification("B", observable1)
    B Observable1
    >>> center.postNotification("B", observable2)

    # no notification, no observable
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", None, None)
    >>> center.postNotification("A", observable1)
    A Observable1
    >>> center.postNotification("A", observable2)
    A Observable2
    >>> center.postNotification("B", observable1)
    B Observable1
    >>> center.postNotification("B", observable2)
    B Observable2
    """

def _testHoldNotifications():
    """
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable1)
    >>> center.addObserver(observer, "notificationCallback", "C", observable2)

    # hold all notifications
    >>> center.holdNotifications()
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    >>> observable2.postNotification("C")
    >>> center.releaseHeldNotifications()
    A Observable1
    B Observable1
    C Observable2

    # hold all notifications of a specific observable
    >>> center.holdNotifications(observable=observable1)
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    >>> observable2.postNotification("C")
    C Observable2
    >>> center.releaseHeldNotifications(observable=observable1)
    A Observable1
    B Observable1

    # hold all notifications of a specific notification
    >>> center.holdNotifications(notification="A")
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    B Observable1
    >>> observable2.postNotification("C")
    C Observable2
    >>> center.releaseHeldNotifications(notification="A")
    A Observable1
    """

def _testAreNotificationsHeld():
    """
    # all held
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable)
    >>> center.holdNotifications()
    >>> center.areNotificationsHeld()
    True
    >>> center.releaseHeldNotifications()
    >>> center.areNotificationsHeld()
    False

    # observable off
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable2)
    >>> center.holdNotifications(observable=observable1)
    >>> center.areNotificationsHeld(observable=observable1)
    True
    >>> center.areNotificationsHeld(observable=observable2)
    False
    >>> center.releaseHeldNotifications(observable=observable1)
    >>> center.areNotificationsHeld(observable=observable1)
    False

    # notification off
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable)
    >>> center.addObserver(observer, "notificationCallback", "B", observable)
    >>> center.holdNotifications(notification="A")
    >>> center.areNotificationsHeld(notification="A")
    True
    >>> center.areNotificationsHeld(notification="B")
    False
    >>> center.releaseHeldNotifications(notification="A")
    >>> center.areNotificationsHeld(notification="A")
    False

    # observer off
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer1 = _TestObserver()
    >>> observer2 = _TestObserver()
    >>> center.addObserver(observer1, "notificationCallback", "A", observable)
    >>> center.addObserver(observer2, "notificationCallback", "A", observable)
    >>> center.holdNotifications(observer=observer1)
    >>> center.areNotificationsHeld(observer=observer1)
    True
    >>> center.areNotificationsHeld(observer=observer2)
    False
    >>> center.releaseHeldNotifications(observer=observer1)
    >>> center.areNotificationsHeld(observer=observer1)
    False
    """

def _testDisableNotifications():
    """
    # disable all notifications
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable1)
    >>> center.addObserver(observer, "notificationCallback", "C", observable2)
    >>> center.disableNotifications()
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    >>> observable2.postNotification("C")
    >>> center.enableNotifications()
    >>> observable1.postNotification("A")
    A Observable1

    # disable all notifications for a specific observable
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable1)
    >>> center.addObserver(observer, "notificationCallback", "C", observable2)
    >>> center.disableNotifications(observable=observable1)
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    >>> observable2.postNotification("C")
    C Observable2
    >>> center.enableNotifications(observable=observable1)
    >>> observable1.postNotification("A")
    A Observable1

    # disable all notifications for a specific notification
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable1)
    >>> center.addObserver(observer, "notificationCallback", "C", observable2)
    >>> center.disableNotifications(notification="A")
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    B Observable1
    >>> observable2.postNotification("C")
    C Observable2
    >>> center.enableNotifications(notification="A")
    >>> observable1.postNotification("A")
    A Observable1

    # disable all notifications for a specific observer
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable1)
    >>> center.addObserver(observer, "notificationCallback", "C", observable2)
    >>> center.disableNotifications(observer=observer)
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    >>> observable2.postNotification("C")
    >>> center.enableNotifications(observer=observer)
    >>> observable1.postNotification("A")
    A Observable1
    """

def _testAreNotificationsDisabled():
    """
    # all off
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable2)
    >>> center.disableNotifications()
    >>> center.areNotificationsDisabled()
    True
    >>> center.enableNotifications()
    >>> center.areNotificationsDisabled()
    False

    # observable off
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable2)
    >>> center.disableNotifications(observable=observable1)
    >>> center.areNotificationsDisabled(observable=observable1)
    True
    >>> center.areNotificationsDisabled(observable=observable2)
    False
    >>> center.enableNotifications(observable=observable1)
    >>> center.areNotificationsDisabled(observable=observable1)
    False

    # notification off
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable2)
    >>> center.disableNotifications(notification="A")
    >>> center.areNotificationsDisabled(notification="A")
    True
    >>> center.areNotificationsDisabled(notification="B")
    False
    >>> center.enableNotifications(notification="A")
    >>> center.areNotificationsDisabled(notification="A")
    False

    # observer off
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer1 = _TestObserver()
    >>> observer2 = _TestObserver()
    >>> center.addObserver(observer1, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer2, "notificationCallback", "A", observable1)
    >>> center.disableNotifications(observer=observer1)
    >>> center.areNotificationsDisabled(observer=observer1)
    True
    >>> center.areNotificationsDisabled(observer=observer2)
    False
    >>> center.enableNotifications(observer=observer1)
    >>> center.areNotificationsDisabled(observer=observer1)
    False
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
