class Color(object):

    """
    This object represents a color. This object is immutable.

    The initial argument can be either a color string as defined in the UFO
    specification or a sequence of (red, green, blue, alpha) components.

    By calling str(colorObject) you will get a UFO compatible color string.
    You can also iterate over the object to create a sequence::

        colorTuple = tuple(colorObject)
    """

    def __init__(self, value):
        if isinstance(value, basestring):
            r, g, b, a = [i.strip() for i in value.split(",")]
            value = []
            for component in (r, g, b, a):
                try:
                    v = int(component)
                    value.append(v)
                    continue
                except ValueError:
                    pass
                v = float(component)
                value.append(v)
        r, g, b, a = value

        color = (("r", r), ("g", g), ("b", b), ("a", a))
        for component, v in color:
            if v < 0 or v > 1:
                raise ValueError("The color for %s (%s) is not between 0 and 1." % (component, str(v)))
        self._r = r
        self._g = g
        self._b = b
        self._a = a

    def __iter__(self):
        attrs = ["r", "g", "b", "a"]
        while attrs:
            attr = attrs[0]
            yield getattr(self, attr)
            attrs = attrs[1:]

    def __str__(self):
        r = _stringify(self._r)
        g = _stringify(self._g)
        b = _stringify(self._b)
        a = _stringify(self._a)
        s = ",".join((r, g, b, a))
        return s

    def __cmp__(self, other):
        if not isinstance(other, Color):
            return False
        return tuple(self) == tuple(other)

    def _get_r(self):
        return self._r

    r = property(_get_r, "The red component.")

    def _get_g(self):
        return self._g

    g = property(_get_g, "The green component.")

    def _get_b(self):
        return self._b

    b = property(_get_b, "The blue component.")

    def _get_a(self):
        return self._a

    a = property(_get_a, "The alpha component.")


def _stringify(v):
    """
    >>> _stringify(1)
    '1'
    >>> _stringify(.1)
    '0.1'
    >>> _stringify(.01)
    '0.01'
    >>> _stringify(.001)
    '0.001'
    >>> _stringify(.0001)
    '0.0001'
    >>> _stringify(.00001)
    '0.00001'
    >>> _stringify(.000001)
    '0'
    >>> _stringify(.000005)
    '0.00001'
    """
    # it's an int
    i = int(v)
    if v == i:
        return str(i)
    # it's a float
    else:
        # find the shortest possible float
        for i in range(1, 6):
            s = "%%.%df" % i
            s = s % v
            if float(s) == v:
                break
        # see if the result can be converted to an int
        f = float(s)
        i = int(f)
        if f == i:
            return str(i)
        # otherwise return the float
        return s

def _test():
    """
    From String:
    >>> tuple(Color("1,1,1,1"))
    (1, 1, 1, 1)
    >>> tuple(Color(".1,.1,.1,.1"))
    (0.10000000000000001, 0.10000000000000001, 0.10000000000000001, 0.10000000000000001)
    >>> tuple(Color("1, 1, 1, 1"))
    (1, 1, 1, 1)
    >>> tuple(Color("0.1 , 0.1, 0.1, 0.1"))
    (0.10000000000000001, 0.10000000000000001, 0.10000000000000001, 0.10000000000000001)

    From Sequence:
    >>> tuple(Color((1, 1, 1, 1)))
    (1, 1, 1, 1)

    Convert to String:
    >>> str(Color((0, 0, 0, 0)))
    '0,0,0,0'
    >>> str(Color((1, 1, 1, 1)))
    '1,1,1,1'
    >>> str(Color((.1, .1, .1, .1)))
    '0.1,0.1,0.1,0.1'

    Convert to Sequence:
    >>> tuple(Color((1, 1, 1, 1)))
    (1, 1, 1, 1)

    Component Attributes:
    >>> c = Color((.1, .2, .3, .4))
    >>> c.r
    0.10000000000000001
    >>> c.g
    0.20000000000000001
    >>> c.b
    0.29999999999999999
    >>> c.a
    0.40000000000000002

    Invalid Component Values:
    >>> Color((-1, 0, 0, 0))
    Traceback (most recent call last):
        ...
    ValueError: The color for r (-1) is not between 0 and 1.
    >>> Color((0, -1, 0, 0))
    Traceback (most recent call last):
        ...
    ValueError: The color for g (-1) is not between 0 and 1.
    >>> Color((0, 0, -1, 0))
    Traceback (most recent call last):
        ...
    ValueError: The color for b (-1) is not between 0 and 1.
    >>> Color((0, 0, 0, -1))
    Traceback (most recent call last):
        ...
    ValueError: The color for a (-1) is not between 0 and 1.
    >>> Color((2, 0, 0, 0))
    Traceback (most recent call last):
        ...
    ValueError: The color for r (2) is not between 0 and 1.
    >>> Color((0, 2, 0, 0))
    Traceback (most recent call last):
        ...
    ValueError: The color for g (2) is not between 0 and 1.
    >>> Color((0, 0, 2, 0))
    Traceback (most recent call last):
        ...
    ValueError: The color for b (2) is not between 0 and 1.
    >>> Color((0, 0, 0, 2))
    Traceback (most recent call last):
        ...
    ValueError: The color for a (2) is not between 0 and 1.
    """

if __name__ == "__main__":
    import doctest
    doctest.testmod()
