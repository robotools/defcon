from defcon.objects.base import BaseDictObject


class Kerning(BaseDictObject):

    """
    This object contains all of the kerning pairs in a font.

    **This object posts the following notifications:**

    ===============  ====
    Name             Note
    ===============  ====
    Kerning.Changed  Posted when the *dirty* attribute is set.
    ===============  ====

    This object behaves like a dict. For example, to get a list of all kerning pairs::

        pairs = kerning.keys()

    To get all pairs including the values::

        for (left, right), value in kerning.items():

    To get the value for a particular pair::

        value = kerning["a", "b"]

    To set the value for a particular pair::

        kerning["a", "b"] = 100

    And so on.

    **Note:** This object is not very smart in the way it handles zero values,
    exceptions, etc. This may change in the future.
    """

    _notificationName = "Kerning.Changed"

    def get(self, pair, default=0):
        return super(Kerning, self).get(pair, default)


def _test():
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
