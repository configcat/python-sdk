__PREDEFINED__ = ["Identifier", 'Email', 'Country']


class User(object):
    """
     The user object for variation evaluation
    """

    def __init__(self, identifier, email=None, country=None, custom=None):
        self.__identifier = identifier if identifier is not None else ''
        self.__data = {'Identifier': identifier, 'Email': email, 'Country': country}
        self.__custom = custom

    def get_identifier(self):
        return self.__identifier

    def get_attribute(self, attribute):
        attribute = str(attribute)
        if attribute in __PREDEFINED__:
            return self.__data[attribute]

        if self.__custom is not None:
            for customField in self.__custom:
                if customField == attribute:
                    return self.__custom[customField]

        return None

    def __str__(self):
        r = '{\n    "Identifier": "%s"' % self.__identifier
        if self.__data['Email'] is not None:
            r += ',\n    "Email": "%s"' % self.__data['Email']
        if self.__data['Country'] is not None:
            r += ',\n    "Country": "%s"' % self.__data['Country']
        if self.__custom is not None:
            r += ',\n    "Custom": {'
            for customField in self.__custom:
                r += '\n        "%s": "%s",' % (customField, self.__custom[customField])
            r += '\n    }'
        r += '\n}'
        return r
