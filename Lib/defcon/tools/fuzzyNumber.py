class FuzzyNumber(object):

    def __init__(self, value, threshold):
        self.value = value
        self.threshold = threshold

    def __repr__(self):
        return '[%d %d]' % (self.value, self.threshold)

    def __cmp__(self, other):
        if abs(self.value - other.value) < self.threshold:
            return 0
        else:
            return cmp(self.value, other.value)