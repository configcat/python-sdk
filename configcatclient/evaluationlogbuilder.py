class EvaluationLogBuilder(object):
    def __init__(self):
        self.indent_level = 0
        self.text = ''

    @staticmethod
    def trunc_comparison_value_if_needed(comparator_text, comparison_value):
        if '(hashed)' in comparator_text:
            if isinstance(comparison_value, list):
                length = len(comparison_value)
                if length > 1:
                    return '[<{} hashed values>]'.format(length)
                return '[<{} hashed value>]'.format(length)

            return '<hashed value>'

        if isinstance(comparison_value, list):
            limit = 10
            length = len(comparison_value)
            if length > limit:
                remaining = length - limit
                if remaining == 1:
                    more_text = "(1 more value)"
                else:
                    more_text = "({} more values)".format(remaining)

                return str(comparison_value[:limit])[:-1] + ', ... ' + more_text + ']'

        return str(comparison_value)

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