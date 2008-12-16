import weakref

class NotificationCenter(object):

    def __init__(self):
        self._observables = {}

    def addObserver(self, observer, callbackString, notification, observable):
        if observable is not None:
            observable = weakref.ref(observable)
        observer = weakref.ref(observer)
        if not self._observables.has_key(notification):
            self._observables[notification] = {}
        observableDict = self._observables[notification]
        if not observableDict.has_key(observable):
            observableDict[observable] = {}
        observerDict = observableDict[observable]
        observerDict[observer] = callbackString

    def removeObserver(self, observer, notification, observable):
        if observable is not None:
            observable = weakref.ref(observable)
        observer = weakref.ref(observer)
        del self._observables[notification][observable][observer]

    def hasObserver(self, observer, notification, observable):
        if observable is not None:
            observable = weakref.ref(observable)
        observer = weakref.ref(observer)
        if not notification not in self._observables:
            return False
        if observable not in self._observables[notification]:
            return False
        if observer not in self._observables[notification][observer]:
            return False
        return True

    def postNotification(self, notification, observable, data=None):
        observableObj = observable
        if observable is not None:
            observable = weakref.ref(observable)
        if self._observables.has_key(notification):
            for observableRef, observerDict in self._observables[notification].items():
                if observable == observableRef:
                    for observerRef, callbackString in observerDict.items():
                        observer = observerRef()
                        callback = getattr(observer, callbackString)
                        n = Notification(notification, observableRef, data)
                        callback(n)


class Notification(object):

    def __init__(self, name, objRef, data):
        self.name = name
        self._objRef = objRef
        self.data = data

    def _get_object(self):
        if self._objRef is not None:
            return self._objRef()
        return None

    object = property(_get_object)

