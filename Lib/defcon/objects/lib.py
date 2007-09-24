from defcon.objects.base import BaseDictObject


class Lib(BaseDictObject):

    _notificationName = "Lib.Changed"


if __name__ == "__main__":
    import doctest
    doctest.testmod()