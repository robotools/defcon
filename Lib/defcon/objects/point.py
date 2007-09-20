class Point(object):

    __slots__ = ['x', 'y', 'segmentType', 'smooth', 'name']

    def __init__(self, (x, y), segmentType=None, smooth=False, name=None):
        self.x = x
        self.y = y
        self.segmentType = segmentType
        self.smooth = smooth
        self.name = name

    def __repr__(self):
        return '<Point position: (%s, %s) type: %s smooth: %s name: %s>' % (self.x, self.y, str(self.segmentType), str(self.smooth), str(self.name))

    def move(self, (x, y)):
        self.x += x
        self.y += y


if __name__ == "__main__":
    import doctest
    doctest.testmod()