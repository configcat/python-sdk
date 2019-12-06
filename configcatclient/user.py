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

    def __str__(self):
        r = '{\n    "Identifier": "%s"' % self.__identifier
        if self.__data['email'] is not None:
            r += ',\n    "Email": "%s"' % self.__data['email']
        if self.__data['country'] is not None:
            r += ',\n    "Country": "%s"' % self.__data['country']
        if self.__custom is not None:
            r += ',\n    "Custom": {'
            for customField in self.__custom:
                r += '\n        "%s": "%s",' % (customField, self.__custom[customField])
            r += '\n    }'
        r += '\n}'
        return r
