from defcon.objects.base import BaseObject


class Kerning(BaseObject):

    _notificationName = "Kerning.Changed"

    def __init__(self, dispatcher=None):
        super(Kerning, self).__init__(dispatcher)
        self._kerning = {}
        self._dirty = False

    def keys(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> keys = font.kerning.keys()
        >>> keys.sort()
        >>> keys
        [('A', 'A'), ('A', 'B')]
        """
        return self._kerning.keys()

    def items(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> items = font.kerning.items()
        >>> items.sort()
        >>> items
        [(('A', 'A'), -100), (('A', 'B'), 100)]
        """
        return self._kerning.items()

    def values(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> values = font.kerning.values()
        >>> values.sort()
        >>> values
        [-100, 100]
        """
        return self._kerning.values()

    def __contains__(self, pair):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> ('A', 'B') in font.kerning
        True
        >>> ('NotInFont', 'NotInFont') in font.kerning
        False
        """
        return pair in self._kerning

    has_key = __contains__

    def get(self, pair, default=0):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> font.kerning.get(('A', 'A'))
        -100
        >>> font.kerning.get(('NotInFont', 'NotInFont'))
        0
        >>> font.kerning.get(('NotInFont', 'NotInFont'), None)
        """
        return self._kerning.get(pair, default)

    def __getitem__(self, pair):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> font.kerning['A', 'A']
        -100
        >>> font.kerning['NotInFont', 'NotInFont']
        Traceback (most recent call last):
            ...
        KeyError: "('NotInFont', 'NotInFont') not in kerning"
        """
        if pair not in self._kerning:
            raise KeyError, '%s not in kerning' % str(pair)
        return self._kerning[pair]

    def __setitem__(self, pair, value):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> font.kerning['NotInFont', 'NotInFont'] = 100
        >>> keys = font.kerning.keys()
        >>> keys.sort()
        >>> keys
        [('A', 'A'), ('A', 'B'), ('NotInFont', 'NotInFont')]
        >>> font.kerning.dirty
        True
        """
        # XXX handle zero!
        self._kerning[pair] = value
        self.dirty = True

    def clear(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> font.kerning.clear()
        >>> font.kerning.keys()
        []
        >>> font.kerning.dirty
        True
        """
        self._kerning.clear()
        self.dirty = True

    def update(self, other):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font
        >>> font = Font(getTestFontPath())
        >>> other = {('X', 'X'):500}
        >>> font.kerning.update(other)
        >>> keys = font.kerning.keys()
        >>> keys.sort()
        >>> keys
        [('A', 'A'), ('A', 'B'), ('X', 'X')]
        >>> font.kerning.dirty
        True
        """
        self._kerning.update(other)
        self.dirty = True


if __name__ == "__main__":
    import doctest
    doctest.testmod()
