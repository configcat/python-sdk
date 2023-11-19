from .config import Comparator
from .utils import get_date_time


class EvaluationLogBuilder(object):
    def __init__(self):
        self.indent_level = 0
        self.text = ''

    @staticmethod
    def trunc_comparison_value_if_needed(comparator, comparison_value):
        if comparator in [Comparator.IS_ONE_OF_HASHED,
                          Comparator.IS_NOT_ONE_OF_HASHED,
                          Comparator.EQUALS_HASHED,
                          Comparator.NOT_EQUALS_HASHED,
                          Comparator.STARTS_WITH_ANY_OF_HASHED,
                          Comparator.NOT_STARTS_WITH_ANY_OF_HASHED,
                          Comparator.ENDS_WITH_ANY_OF_HASHED,
                          Comparator.NOT_ENDS_WITH_ANY_OF_HASHED,
                          Comparator.ARRAY_CONTAINS_ANY_OF_HASHED,
                          Comparator.ARRAY_NOT_CONTAINS_ANY_OF_HASHED]:
            if isinstance(comparison_value, list):
                length = len(comparison_value)
                if length > 1:
                    return '[<{} hashed values>]'.format(length)
                return '[<{} hashed value>]'.format(length)

            return "'<hashed value>'"

        if isinstance(comparison_value, list):
            length_limit = 10
            length = len(comparison_value)
            if length > length_limit:
                remaining = length - length_limit
                if remaining == 1:
                    more_text = "<1 more value>"
                else:
                    more_text = "<{} more values>".format(remaining)

                return str(comparison_value[:length_limit])[:-1] + ', ... ' + more_text + ']'

            return str(comparison_value)

        if comparator in [Comparator.BEFORE_DATETIME, Comparator.AFTER_DATETIME]:
            time = get_date_time(comparison_value)
            return "'%s' (%sZ UTC)" % (str(comparison_value), time.strftime('%Y-%m-%dT%H:%M:%S.%f')[:-3])

        return "'%s'" % str(comparison_value)

    def increase_indent(self):
        self.indent_level += 1
        return self

    def decrease_indent(self):
        self.indent_level = max(0, self.indent_level - 1)
        return self

    def append(self, text):
        self.text += text
        return self

    def new_line(self, text=None):
        self.text += '\n' + '  ' * self.indent_level
        if text:
            self.text += text
        return self

    def __str__(self):
        return self.text
