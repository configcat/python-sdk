import json

__PREDEFINED__ = ['Identifier', 'Email', 'Country']


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

        return self.__custom.get(attribute) if self.__custom else None

    def __str__(self):
        dump = {
            'Identifier': self.__identifier,
            'Email': self.__data.get('Email'),
            'Country': self.__data.get('Country'),
            'Custom': self.__custom,
        }
        return json.dumps(dump, indent=4)
