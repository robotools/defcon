from defcon.objects.base import BaseObject


class Features(BaseObject):

    """
    This object contais the test represening features in the font.

    **This object posts the following notifications:**

    ================
    Name
    ================
    Features.Changed
    Features.TextChanged
    ================
    """

    changeNotificationName = "Features.Changed"
    representationFactories = {}

    def __init__(self):
        super(Features, self).__init__()
        self._dirty = False
        self._text = None

    def _set_text(self, value):
        oldValue = self._text
        if oldValue == value:
            return
        self._text = value
        self.postNotification("Features.TextChanged", data=dict(oldValue=oldValue, newValue=value))
        self.dirty = True

    def _get_text(self):
        return self._text

    text = property(_get_text, _set_text, doc="The raw feature text. Setting this post *Features.TextChanged* and *Features.Changed* notifications.")

