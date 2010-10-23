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
        # disabled
        if (observable, notification) in self._disabled:
            return
        if observable in self._disabled:
            return
        # held
        if (observable, notification) in self._holds:
            n = (notification, observable, data)
            if not self._holds[observable, notification]["notifications"] or self._holds[observable, notification]["notifications"][-1] != n:
                self._holds[observable, notification]["notifications"].append(n)
            return
        if observable in self._holds:
            n = (notification, observable, data)
            if not self._holds[observable]["notifications"] or self._holds[observable]["notifications"][-1] != n:
                self._holds[observable]["notifications"].append(n)
            return
        # post
        if notification in self._observables:
            for observableRef, observerDict in self._observables[notification].items():
                if observable == observableRef:
                    for observerRef, methodName in observerDict.items():
                        observer = observerRef()
                        # disabled for observer
                        if self._disabled:
                            if (observableRef, notification, observerRef) in self._disabled:
                                continue
                            elif (observableRef, observerRef) in self._disabled:
                                continue
                            elif (notification, observerRef) in self._disabled:
                                continue
                        callback = getattr(observer, methodName)
                        n = Notification(notification, observableRef, data)
                        callback(n)

    def holdNotificationsForObservable(self, observable, notification=None):
        """
        Hold all notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to.
        * **notification** The name of the notification. This is optional.
          If no *notification* is given, *all* notifications for *observable*
          will be held.

        Held notifications will be posted after the a matching *notification*
        and *observable* have been passed to :meth:`Notification.releaseHeldNotificationsForObservable`.
        This object will retain a count of how many times it has been told to
        hold notifications for *notification* and *observable*. It will not
        post the notifications until the *notification* and *observable*
        have been released the same number of times.
        """
        observable = weakref.ref(observable)
        if notification is not None:
            key = (observable, notification)
        else:
            key = observable
        if key not in self._holds:
            self._holds[key] = dict(holdCount=0, notifications=[])
        self._holds[key]["holdCount"] += 1

    def releaseHeldNotificationsForObservable(self, observable, notification=None):
        """
        Release all held notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to.
        * **notification** The name of the notification. This is optional.
        """
        observableObj = observable
        observable = weakref.ref(observable)
        if notification is not None:
            key = (observable, notification)
        else:
            key = observable
        self._holds[key]["holdCount"] -= 1
        if self._holds[key]["holdCount"] == 0:
            notifications = self._holds[key]["notifications"]
            del self._holds[key]
            for notification, o, data in notifications:
                self.postNotification(notification, observableObj, data)

    def areNotificationsHeldForObservable(self, observable, notification=None):
        """
        Returns a boolean indicating if notifications posted to all objects observing
        **notification** in **observable** are being held.

        * **observable** The object that the notification belongs to.
        * **notification** The name of the notification. This is optional.
        """
        if (observable, notification) in self._holds:
            return True
        return weakref.ref(observable) in self._holds

    def disableNotificationsForObservable(self, observable, notification=None, observer=None):
        """
        Disable all posts of **notification** from **observable** posted
        to **observer** observing.

        * **observable** The object that the notification belongs to.
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
        observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = self._makeDisableKey(observable, notification=notification, observer=observer)
        if key not in self._disabled:
            self._disabled[key] = 0
        self._disabled[key] += 1

    def enableNotificationsForObservable(self, observable, notification=None, observer=None):
        """
        Enable notifications posted to all objects observing
        **notification** in **observable**.

        * **observable** The object that the notification belongs to.
        * **notification** The name of the notification. This is optional.
        * **observer** The observer. This is optional.
        """
        observableObj = observable
        observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = self._makeDisableKey(observable, notification=notification, observer=observer)
        self._disabled[key] -= 1
        if self._disabled[key] == 0:
            del self._disabled[key]

    def areNotificationsDisabledForObservable(self, observable, notification=None, observer=None):
        """
        Returns a boolean indicating if notifications posted to all objects observing
        **notification** in **observable** are disabled.

        * **observable** The object that the notification belongs to.
        * **notification** The name of the notification. This is optional.
        * **observer** The observer. This is optional.
        """
        observable = weakref.ref(observable)
        if observer is not None:
            observer = weakref.ref(observer)
        key = self._makeDisableKey(observable, notification=notification, observer=observer)
        return key in self._disabled

    def _makeDisableKey(self, observable, notification=None, observer=None):
        key = [observable]
        if notification is not None:
            key.append(notification)
        if observer is not None:
            key.append(observer)
        if len(key) == 1:
            key = key[0]
        else:
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
