"""
Contributed by Frederik Berlaen.
"""

from __future__ import division
from math import sqrt

def _distance((x1, y1), (x2, y2)):
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def joinSegments((on1X, on1Y),
    (off1X, off1Y), (off2X, off2Y), (on2X, on2Y),
    (off3X, off3Y), (off4X, off4Y), (on3X, on3Y)):
    """
    >>> joinSegments(
    ...    (0, 0),
    ...    (0, 138), (112, 250), (250, 250),
    ...    (250, 388), (500, 138), (500, 0)
    ...    )
    ((0.0, 195.16147160748713), (500.0, 471.16147160748704), (500, 0))
    >>> print "need more tests!"
    """
    # first calculate an aproximaly t
    d1 = _distance((on2X, on2Y), (off2X, off2Y))
    d2 = _distance((off3X, off3Y), (off2X, off2Y))
    if d2 == 0:
        t = 0
    else:
        t = d1 / d2
    # just multiply the first handle of the first curve by t
    if t == 0:
        p2X = on1X + (off1X - on1X)
        p2Y = on1Y + (off1Y - on1Y)
    else:
        p2X = on1X + (off1X - on1X) * (1 / t)
        p2Y = on1Y + (off1Y - on1Y) * (1 / t)
    # and the last handle of the last curve by t
    if t == 1:
        p3X = on3X + (off4X - on3X)
        p3Y = on3Y + (off4Y - on3Y)
    else:
        p3X = on3X + (off4X - on3X) * (1 / (1 - t))
        p3Y = on3Y + (off4Y - on3Y) * (1 / (1 - t))
    return (p2X, p2Y), (p3X, p3Y), (on3X, on3Y)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
