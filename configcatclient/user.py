import json

__PREDEFINED__ = ['Identifier', 'Email', 'Country']

from collections import OrderedDict


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
        dump = OrderedDict([
            ('Identifier', self.__identifier),
            ('Email', self.__data.get('Email')),
            ('Country', self.__data.get('Country'))
        ])
        if self.__custom:
            dump.update(self.__custom)

        filtered_dump = OrderedDict([(k, v) for k, v in dump.items() if v is not None])
        return json.dumps(filtered_dump, separators=(',', ':'))
