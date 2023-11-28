import json

__PREDEFINED__ = ['Identifier', 'Email', 'Country']

from collections import OrderedDict
from datetime import datetime


class User(object):
    """
    User Object. Contains user attributes which are used for evaluating targeting rules and percentage options.
    """

    def __init__(self, identifier, email=None, country=None, custom=None):
        """
        Initialize a User object.

        Args:
            identifier: The unique identifier of the user or session (e.g. email address, primary key, session ID, etc.)
            email: Email address of the user.
            country: Country of the user.
            custom: Custom attributes of the user for advanced targeting rule definitions (e.g. role, subscription type, etc.)

            All comparators support string values as User Object attribute (in some cases they need to be provided in a
            specific format though, see below), but some of them also support other types of values. It depends on the
            comparator how the values will be handled. The following rules apply:

            Text-based comparators (EQUALS, IS_ONE_OF, etc.)
            * accept string values,
            * all other values are automatically converted to string
              (a warning will be logged but evaluation will continue as normal).

            SemVer-based comparators (IS_ONE_OF_SEMVER, LESS_THAN_SEMVER, GREATER_THAN_SEMVER, etc.)
            * accept string values containing a properly formatted, valid semver value,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).

            Number-based comparators (EQUALS_NUMBER, LESS_THAN_NUMBER, GREATER_THAN_OR_EQUAL_NUMBER, etc.)
            * accept float values and all other numeric values which can safely be converted to float,
            * accept string values containing a properly formatted, valid float value,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).

            Date time-based comparators (BEFORE_DATETIME / AFTER_DATETIME)
            * accept datetime values, which are automatically converted to a second-based Unix timestamp
              (datetime values with naive timezone are considered to be in UTC),
            * accept float values representing a second-based Unix timestamp
              and all other numeric values which can safely be converted to float,
            * accept string values containing a properly formatted, valid float value,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).

            String array-based comparators (ARRAY_CONTAINS_ANY_OF / ARRAY_NOT_CONTAINS_ANY_OF)
            * accept arrays of strings,
            * accept string values containing a valid JSON string which can be deserialized to an array of strings,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).
        """
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
        def serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()

            raise TypeError("Type not serializable")

        dump = OrderedDict([
            ('Identifier', self.__identifier),
            ('Email', self.__data.get('Email')),
            ('Country', self.__data.get('Country'))
        ])
        if self.__custom:
            dump.update(self.__custom)

        filtered_dump = OrderedDict([(k, v) for k, v in dump.items() if v is not None])
        return json.dumps(filtered_dump, separators=(',', ':'), default=serializer)
