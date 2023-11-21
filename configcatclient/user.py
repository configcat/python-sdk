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

            The set of allowed attribute values depends on the comparison type of the condition which references the User
            Object attribute. String values are supported by all comparison types (in some cases they need to be provided in a
            specific format though). Some comparison types work with other types of values, as described below.

            Text-based comparisons (EQUALS, IS_ONE_OF, etc.)
            * accept string values,
            * all other values are automatically converted to string
              (a warning will be logged but evaluation will continue as normal).

            SemVer-based comparisons (IS_ONE_OF_SEMVER, LESS_THAN_SEMVER, GREATER_THAN_SEMVER, etc.)
            * accept string values containing a properly formatted, valid semver value,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).

            Number-based comparisons (EQUALS_NUMBER, LESS_THAN_NUMBER, GREATER_THAN_OR_EQUAL_NUMBER, etc.)
            * accept float values and all other numeric values which can safely be converted to float,
            * accept string values containing a properly formatted, valid float value,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).

            Date time-based comparisons (BEFORE_DATETIME / AFTER_DATETIME)
            * accept datetime values, which are automatically converted to a second-based Unix timestamp
              (datetime values with naive timezone are considered to be in UTC),
            * accept float values representing a second-based Unix timestamp
              and all other numeric values which can safely be converted to float,
            * accept string values containing a properly formatted, valid float value,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).

            String array-based comparisons (ARRAY_CONTAINS_ANY_OF / ARRAY_NOT_CONTAINS_ANY_OF)
            * accept arrays of strings,
            * accept string values containing a valid JSON string which can be deserialized to an array of strings,
            * all other values are considered invalid
              (a warning will be logged and the currently evaluated targeting rule will be skipped).

            In cases where a non-string attribute value needs to be converted to string during evaluation,
            it will always be done using the same format which is accepted by the comparisons.
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
