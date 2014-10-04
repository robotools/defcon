"""
Contributed by Frederik Berlaen.
"""


from math import sqrt

def _distance(xxx_todo_changeme, xxx_todo_changeme1):
    (x1, y1) = xxx_todo_changeme
    (x2, y2) = xxx_todo_changeme1
    return sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def joinSegments(xxx_todo_changeme2, xxx_todo_changeme3, xxx_todo_changeme4, xxx_todo_changeme5, xxx_todo_changeme6, xxx_todo_changeme7, xxx_todo_changeme8):
    """
    >>> joinSegments(
    ...    (0, 0),
    ...    (0, 138), (112, 250), (250, 250),
    ...    (250, 388), (500, 138), (500, 0)
    ...    )
    ((0.0, 195.16147160748713), (500.0, 471.16147160748704), (500, 0))
    >>> print "need more tests!"
    """
    (on1X, on1Y) = xxx_todo_changeme2
    (off1X, off1Y) = xxx_todo_changeme3
    (off2X, off2Y) = xxx_todo_changeme4
    (on2X, on2Y) = xxx_todo_changeme5
    (off3X, off3Y) = xxx_todo_changeme6
    (off4X, off4Y) = xxx_todo_changeme7
    (on3X, on3Y) = xxx_todo_changeme8
    if (on1X, on1Y) == (off1X, off1Y) and (off2X, off2Y) == (on2X, on2Y) == (off3X, off3Y) and  (off4X, off4Y) == (on3X, on3Y):
        ## a two line segments
        return (on1X, on1Y), (off4X, off4Y), (on3X, on3Y)
    if (on1X, on1Y) == (off1X, off1Y) and (off2X, off2Y) == (on2X, on2Y):
        ## first is a line segement
        d1 = _distance((on1X, on1Y), (off2X, off2Y))
        d2 = d1 + _distance((on2X, on2Y), (off3X, off3Y))
        if d1 == 0:
            x, y = off3X, off3Y
        else:
            factor = d2 / d1
            x = on1X + (off2X - on1X) * factor
            y = on1Y + (off2Y - on1Y) * factor
        return (x, y), (off4X, off4Y), (on3X, on3Y)
        
    if (on2X, on2Y) == (off3X, off3Y) and (off4X, off4Y) == (on3X, on3Y):
        ## last is a line segment
        d1 = _distance((on3X, on3Y), (off3X, off3Y))
        d2 = d1 + _distance((on2X, on2Y), (off2X, off2Y))
        if d1 == 0:
            x, y = off2X, off2Y
        else:
            factor = d2 / d1
            x = on3X + (off3X - on3X) * factor
            y = on3Y + (off3Y - on3Y) * factor
        return (off1X, off1Y), (x, y), (on3X, on3Y)
    
    if (off2X, off2Y) == (on2X, on2Y) == (off3X, off3Y) or (off2X, off2Y) == (on2X, on2Y) or (on2X, on2Y) == (off3X, off3Y):
        ## one or more bcps are on the joined point
        return (off1X, off1Y), (off4X, off4Y), (on3X, on3Y)
    
    if (on1X, on1Y) == (off1X, off1Y):
        off1X = off1X + (off2X - off1X) * .1
        off1Y = off1Y + (off2Y - off1Y) * .1
    
    if (on3X, on3Y) == (off4X, off4Y):
        off4X = off4X + (off3X - off4X) * .1
        off4Y = off4Y + (off3Y - off4Y) * .1
    
    # first calculate an aproximaly t
    d1 = _distance((on2X, on2Y), (off2X, off2Y))
    d2 = d1 + _distance((off3X, off3Y), (on2X, on2Y))
    
    if d2 == 0:
        t = 0
    else:
        t = d1 / d2
    
    # cut of the extreme t values
    error = .15
    if t < error:
        t = error
    elif t > 1 - error:
        t = 1 - error
    
    # just multiply the first handle of the first curve by t
    p2X = on1X + (off1X - on1X) * (1 / t)
    p2Y = on1Y + (off1Y - on1Y) * (1 / t)
    # and the last handle of the last curve by t

    p3X = on3X + (off4X - on3X) * (1 / (1 - t))
    p3Y = on3Y + (off4Y - on3Y) * (1 / (1 - t))

    return (p2X, p2Y), (p3X, p3Y), (on3X, on3Y)

if __name__ == "__main__":
    import doctest
    doctest.testmod()
