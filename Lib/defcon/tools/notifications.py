import weakref

class NotificationCenter(object):

    def __init__(self):
        self._observables = {}

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
        if not self._observables.has_key(notification):
            self._observables[notification] = {}
        observableDict = self._observables[notification]
        if not observableDict.has_key(observable):
            observableDict[observable] = {}
        observerDict = observableDict[observable]
        observerDict[observer] = methodName

    def removeObserver(self, observer, notification, observable):
        """
        Remove an observer from this notification dispatcher.

        * **observer** A registered object.
        * **notification** The notification that teh observer was registered
          to be notified of.
        * **observable** The object being observed.
        """
        if observable is not None:
            observable = weakref.ref(observable)
        observer = weakref.ref(observer)
        del self._observables[notification][observable][observer]

    def hasObserver(self, observer, notification, observable):
        """
        Returns a boolean indicating is the **observer** is registered for **notification** posted by **observable**.
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
        Post a notification to all objects observing **notification** in **observable**.

        * **notification** The name of the notification.
        * **observable** The object that the notification belongs to.
        * **data** Arbitrary data that will be stored in the :class:`Notification` object.

        This will create a :class:`Notification` object and post it to all relevant observers.
        """
        observableObj = observable
        if observable is not None:
            observable = weakref.ref(observable)
        if self._observables.has_key(notification):
            for observableRef, observerDict in self._observables[notification].items():
                if observable == observableRef:
                    for observerRef, methodName in observerDict.items():
                        observer = observerRef()
                        callback = getattr(observer, methodName)
                        n = Notification(notification, observableRef, data)
                        callback(n)


class Notification(object):

    """An object that wraps notification data."""

    def __init__(self, name, objRef, data):
        self._name = name
        self._objRef = objRef
        self._data = data

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
