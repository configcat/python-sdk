import logging
import sys


class Logger(logging.LoggerAdapter):
    def __init__(self, name, hooks):
        super(Logger, self).__init__(logging.getLogger(name), {})
        self._hooks = hooks

    def process(self, msg, kwargs):
        # Remove event_id from kwargs (as it's not a built-in argument expected by the logging framework)
        # and put it in the extra dict so users can access it without parsing.
        event_id = kwargs.pop('event_id', 0)
        extra = kwargs.setdefault('extra', {})
        extra['event_id'] = event_id

        # Include the event_id in the message.
        return "[" + str(event_id) + "] " + msg, kwargs

    def error(self, msg, *args, **kwargs):
        self._hooks.invoke_on_error(Logger.format(msg, args))
        super(Logger, self).error(msg, *args, **kwargs)

    def exception(self, msg, *args, **kwargs):
        self._hooks.invoke_on_error(Logger.format(msg, args, sys.exc_info()[1]))
        super(Logger, self).exception(msg, *args, **kwargs)

    @staticmethod
    def format(msg, args, exc=None):
        msg = msg % args if len(args) > 0 else msg
        return msg if exc is None else msg + '\n' + str(exc)
