from defcon.objects.base import BaseDictObject


class Groups(BaseDictObject):

    _notificationName = "Groups.Changed"


if __name__ == "__main__":
    import doctest
    doctest.testmod()