from defcon.objects.base import BaseDictObject


class Kerning(BaseDictObject):

    _notificationName = "Kerning.Changed"

    def get(self, pair, default=0):
        return super(Kerning, self).get(pair, default)

    def _test(self):
        """
        >>> from defcon.test.testTools import getTestFontPath
        >>> from defcon.objects.font import Font

        # keys
        >>> font = Font(getTestFontPath())
        >>> keys = font.kerning.keys()
        >>> keys.sort()
        >>> keys
        [('A', 'A'), ('A', 'B')]

        # items
        >>> font = Font(getTestFontPath())
        >>> items = font.kerning.items()
        >>> items.sort()
        >>> items
        [(('A', 'A'), -100), (('A', 'B'), 100)]

        # values
        >>> font = Font(getTestFontPath())
        >>> values = font.kerning.values()
        >>> values.sort()
        >>> values
        [-100, 100]

        # __contains__
        >>> font = Font(getTestFontPath())
        >>> ('A', 'B') in font.kerning
        True
        >>> ('NotInFont', 'NotInFont') in font.kerning
        False

        # get
        >>> font = Font(getTestFontPath())
        >>> font.kerning.get(('A', 'A'))
        -100
        >>> font.kerning.get(('NotInFont', 'NotInFont'), 0)
        0

        # __getitem__
        >>> font = Font(getTestFontPath())
        >>> font.kerning['A', 'A']
        -100
        >>> font.kerning['NotInFont', 'NotInFont']
        Traceback (most recent call last):
            ...
        KeyError: ('NotInFont', 'NotInFont')

        # __setitem__
        >>> font = Font(getTestFontPath())
        >>> font.kerning['NotInFont', 'NotInFont'] = 100
        >>> keys = font.kerning.keys()
        >>> keys.sort()
        >>> keys
        [('A', 'A'), ('A', 'B'), ('NotInFont', 'NotInFont')]
        >>> font.kerning.dirty
        True

        # clear
        >>> font = Font(getTestFontPath())
        >>> font.kerning.clear()
        >>> font.kerning.keys()
        []
        >>> font.kerning.dirty
        True

        # update
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


if __name__ == "__main__":
    import doctest
    doctest.testmod()
