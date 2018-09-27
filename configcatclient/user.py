__PREDEFINED__ = ["key", 'email', 'country']


class User(object):
    """
     The user object for variation evaluation
    """

    def __init__(self, key, email=None, country=None, custom=None):
        self.__key = key
        self.__data = {'key': key, 'email': email, 'country': country}
        self.__custom = custom

    def get_key(self):
        return self.__key

    def get_attribute(self, attribute):
        attribute = str(attribute).lower()
        if attribute in __PREDEFINED__:
            return self.__data[attribute]

        if self.__custom is not None:
            for customField in self.__custom:
                if customField.lower() == attribute:
                    return self.__custom[customField]

        return None
