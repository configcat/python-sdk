from .interfaces import ConfigCatLogger, LogLevel


def _format_message(message, level):
    return 'ConfigCat - [%s] - %s' % (level, message)


class ConfigCatConsoleLogger(ConfigCatLogger):

    def error(self, message):
        if self.log_level >= LogLevel.ERROR:
            print('\033[91m' + _format_message(message, 'ERROR'))

    def warning(self, message):
        if self.log_level >= LogLevel.WARNING:
            print('\033[93m' + _format_message(message, 'WARNING'))

    def info(self, message):
        if self.log_level >= LogLevel.INFO:
            print(_format_message(message, 'INFO'))
