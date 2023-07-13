class LogBuilder(object):
    def __init__(self):
        self.indent_level = 0
        self.text = ''

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
