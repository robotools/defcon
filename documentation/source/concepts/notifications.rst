.. highlight:: python

.. _Notifications:

=============
Notifications
=============

defcon uses something similar to the `Observer Pattern <http://en.wikipedia.org/wiki/Observer_pattern>`_ for inter-object communication and object observation. This abstraction allows you to cleanly listen for particular events happening in particular objects. You don't need to wire up lots of hooks into the various objects or establish complex circular relationships thoughout your interface code. Rather, you register to be notified when something happens in an object. In defcon, these are referred to as *notifications*. For example, I want to be notified when the my font changes::

    class MyInterface(object):

        # random code here, blah, blah.

        def setGlyph(self, glyph):
            glyph.addObserver(self, "glyphChangedCallback", "Glyph.Changed")

        def glyphChangedCallback(self, notification):
            glyph = notification.object
            print("the glyph (%s) changed!" % glyph.name)

When the glyph is changed in anyway by anyone, it posts a "Glyph.Changed" notification to all registered observers. My method above is called when this happens and I can react as needed.

The :ref:`NotificationCenter` object implements all of this. However, all objects derived from :class:`dercon.BaseObject` have a simplified API for tapping into notifications. Each object posts its own unique notifications, so look at the relevant reference for information about the available notifications.

Don't Forget removeObserver
---------------------------

The only real gotcha in this is that you must remove the observer from the observed object when the observation is no longer needed. If you don't do this and the observed object is changed, it will try to post a notification to the object you have discarded. That could lead to trouble.