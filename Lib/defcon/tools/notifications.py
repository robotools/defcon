import weakref

class NotificationCenter(object):

    def __init__(self):
        self._observables = {}
        self._holds = {}
        self._disabled = {}

    def addObserver(self, observer, methodName, notification, observable):
        """
        Add an observer to this notification dispatcher.

        * **observer** An object that can be referenced with weakref.
        * **methodName** A string epresenting the method to be called
          when the notification is posted.
        * **notification** The notification that teh observer should
          be notified of.
        * **observable** The object to observe.

        The method that will be called as a result of the action
        must accept a single *notification* argument. This will
        be a :class:`Notification` object.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        observer = weakref.ref(observer)
        if notification not in self._observables:
            self._observables[notification] = {}
        observableDict = self._observables[notification]
        if observable not in observableDict:
            observableDict[observable] = {}
        observerDict = observableDict[observable]
        observerDict[observer] = methodName

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
        observer = weakref.ref(observer)
        del self._observables[notification][observable][observer]

    def hasObserver(self, observer, notification, observable):
        """
        Returns a boolean indicating is the **observer** is registered
        for **notification** posted by **observable**.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        observer = weakref.ref(observer)
        if notification not in self._observables:
            return False
        if observable not in self._observables[notification]:
            return False
        if observer not in self._observables[notification][observable]:
            return False
        return True

    def postNotification(self, notification, observable, data=None):
        """
        Post a notification to all objects observing **notification**
        in **observable**.

        * **notification** The name of the notification.
        * **observable** The object that the notification belongs to.
        * **data** Arbitrary data that will be stored in the :class:`Notification` object.

        This will create a :class:`Notification` object and post it to
        all relevant observers.
        """
        observableObj = observable
        if observable is not None:
            observable = weakref.ref(observable)
        # check for some known combinations in the holds and disableds
        if self._holds or self._disabled:
            possibilities = [
                (None, None, None),
                (observable, None, None),
                (None, None, notification),
                (observable, None, notification)
            ]
            for possibleObservable, possibleObserver, possibleNotification in possibilities:
                key = self._makeHoldAndDisableKey(observable=possibleObservable, observer=possibleObserver, notification=possibleNotification)
                if key in self._disabled:
                    return
                if key in self._holds:
                    n = (notification, observable, data)
                    if not self._holds[key]["notifications"] or self._holds[key]["notifications"][-1] != n:
                        self._holds[key]["notifications"].append(n)
                    return
        # post
        if notification in self._observables:
            for observableRef, observerDict in self._observables[notification].items():
                if observable == observableRef or observable is None:
                    for observerRef, methodName in observerDict.items():
                        observer = observerRef()
                        # check the holds and disableds
                        if self._disabled:
                            possibilities = [
                                (None, observerRef, None),
                                (observableRef, observerRef, None),
                                (None, observerRef, notification),
                                (observableRef, observerRef, notification),
                            ]
                            skip = False
                            for key in possibilities:
                                if key in self._disabled:
                                    break
                                    skip = True
                                if key in self._holds:
                                    n = (notification, observable, data)
                                    if not self._holds[key]["notifications"] or self._holds[key]["notifications"][-1] != n:
                                        self._holds[key]["notifications"].append(n)
                                    skip = True
                                    break
                            if skip:
                                continue
                        callback = getattr(observer, methodName)
                        n = Notification(notification, observableRef, data)
                        callback(n)

    def holdNotifications(self, observable=None, notification=None):
        """
        Hold all notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to. This is optional.
          If no *observable* is given, *all* *notifications* will be held.
        * **notification** The name of the notification. This is optional.
          If no *notification* is given, *all* notifications for *observable*
          will be held.

        Held notifications will be posted after the matching *notification*
        and *observable* have been passed to :meth:`Notification.releaseHeldNotifications`.
        This object will retain a count of how many times it has been told to
        hold notifications for *notification* and *observable*. It will not
        post the notifications until the *notification* and *observable*
        have been released the same number of times.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        key = self._makeHoldAndDisableKey(observable=observable, notification=notification)
        if key not in self._holds:
            self._holds[key] = dict(holdCount=0, notifications=[])
        self._holds[key]["holdCount"] += 1

    def releaseHeldNotifications(self, observable=None, notification=None):
        """
        Release all held notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to. This is optional.
        * **notification** The name of the notification. This is optional.
        """
        observableObj = observable
        if observable is not None:
            observable = weakref.ref(observable)
        key = self._makeHoldAndDisableKey(observable=observable, notification=notification)
        self._holds[key]["holdCount"] -= 1
        if self._holds[key]["holdCount"] == 0:
            notifications = self._holds[key]["notifications"]
            del self._holds[key]
            for notification, o, data in notifications:
                self.postNotification(notification, observableObj, data)

    def areNotificationsHeld(self, observable=None, notification=None):
        """
        Returns a boolean indicating if notifications posted to all objects observing
        **notification** in **observable** are being held.

        * **observable** The object that the notification belongs to. This is optional.
        * **notification** The name of the notification. This is optional.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        return key in self._holds

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
        key = self._makeHoldAndDisableKey(observable, notification=notification, observer=observer)
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
        observableObj = observable
        if observable is not None:
            observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = self._makeHoldAndDisableKey(observable, notification=notification, observer=observer)
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
        key = self._makeHoldAndDisableKey(observable, notification=notification, observer=observer)
        return key in self._disabled

    def _makeHoldAndDisableKey(self, observable, notification=None, observer=None):
        key = [observable]
        key.append(notification)
        key.append(observer)
        key = tuple(key)
        return key


class Notification(object):

    """An object that wraps notification data."""

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


# -----
# Tests
# -----

class _TestObserver(object):

    def notificationCallback(self, notification):
        print notification.name, notification.object.name


class _TestObservable(object):

    def __init__(self, center, name):
        self.center = center
        self.name = name

    def postNotification(self, name):
        self.center.postNotification(name, self)


def _testAddObserver():
    """
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable)
    >>> center.hasObserver(observer, "A", observable)
    True
    >>> center.hasObserver(observer, "B", observable)
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
    """

def _testPostNotification():
    """
    >>> center = NotificationCenter()
    >>> observable = _TestObservable(center, "Observable")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable)
    >>> observable.postNotification("A")
    A Observable
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

def _testDisableNotifications():
    """
    >>> center = NotificationCenter()
    >>> observable1 = _TestObservable(center, "Observable1")
    >>> observable2 = _TestObservable(center, "Observable2")
    >>> observer = _TestObserver()
    >>> center.addObserver(observer, "notificationCallback", "A", observable1)
    >>> center.addObserver(observer, "notificationCallback", "B", observable1)
    >>> center.addObserver(observer, "notificationCallback", "C", observable2)

    # disable all notifications
    >>> center.disableNotifications()
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    >>> observable2.postNotification("C")
    >>> center.enableNotifications()
    >>> observable1.postNotification("A")
    A Observable1

    # disable all notifications for a specific observable
    >>> center.disableNotifications(observable=observable1)
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    >>> observable2.postNotification("C")
    C Observable2
    >>> center.enableNotifications(observable=observable1)
    >>> observable1.postNotification("A")
    A Observable1

    # disable all notifications for a specific notification
    >>> center.disableNotifications(notification="A")
    >>> observable1.postNotification("A")
    >>> observable1.postNotification("B")
    B Observable1
    >>> observable2.postNotification("C")
    C Observable2
    >>> center.enableNotifications(notification="A")
    >>> observable1.postNotification("A")
    A Observable1
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
