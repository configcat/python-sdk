__PREDEFINED__ = ["identifier", 'email', 'country']


class User(object):
    """
     The user object for variation evaluation
    """

    def __init__(self, identifier, email=None, country=None, custom=None):
        self.__identifier = identifier
        self.__data = {'identifier': identifier, 'email': email, 'country': country}
        self.__custom = custom

    def get_identifier(self):
        return self.__identifier

    def get_attribute(self, attribute):
        attribute = str(attribute).lower()
        if attribute in __PREDEFINED__:
            return self.__data[attribute]

        if self.__custom is not None:
            for customField in self.__custom:
                if customField.lower() == attribute:
                    return self.__custom[customField]

        return None
