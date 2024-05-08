class NoDefaultLocale(Exception):
    def __init__(self, msg="Default locales is not set!", *args):
        super().__init__(msg, *args)


class UnableToFindPrimaryKey(Exception):
    pass
