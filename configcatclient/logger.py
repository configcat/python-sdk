import logging


class Logger(object):
    def __init__(self, name, hooks):
        self._hooks = hooks
        self._logger = logging.getLogger(name)

    def debug(self, msg, *args, **kwargs):
        self._logger.debug(msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        self._logger.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        self._hooks.invoke_on_error(msg)
        self._logger.error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self.error(msg, *args, **kwargs)
