import sys
import inspect
from qualname import qualname
from datetime import datetime

try:
    from datetime import timezone
except ImportError:
    import pytz as timezone  # On Python 2.7, datetime.timezone is not available. We use pytz instead.

epoch_time = datetime(1970, 1, 1, tzinfo=timezone.utc)
distant_future = sys.float_info.max
distant_past = 0


def get_class_from_method(method):
    method_class = sys.modules.get(method.__module__)
    if method_class is None:
        return None
    for name in qualname(method).split('.')[:-1]:
        method_class = getattr(method_class, name)
    if not inspect.isclass(method_class):
        return None
    return method_class


def get_class_from_stack_frame(frame):
    args, _, _, value_dict = inspect.getargvalues(frame)
    # we check the first parameter for the frame function is
    # named 'self' or 'cls'
    if len(args):
        if args[0] == 'self':
            # in that case, 'self' will be referenced in value_dict
            instance = value_dict.get(args[0], None)
            if instance:
                # return its class
                return getattr(instance, '__class__', None)
        if args[0] == 'cls':
            # return the class
            return value_dict.get(args[0], None)

    # return None otherwise
    return None


def method_is_called_from(method, level=1):
    """
    Checks if the current method is being called from a certain method.
    """
    stack_info = inspect.stack()[level + 1]
    frame = stack_info[0]
    calling_method_name = frame.f_code.co_name
    expected_method_name = method.__name__
    if calling_method_name != expected_method_name:
        return False

    calling_class = get_class_from_stack_frame(frame)
    expected_class = get_class_from_method(method)
    if calling_class == expected_class:
        return True
    return False


def get_utc_now():
    return datetime.now(timezone.utc)


def get_seconds_since_epoch(date_time):
    # if there is no timezone info, assume UTC
    if date_time.tzinfo is None:
        date_time = date_time.replace(tzinfo=timezone.utc)

    return (date_time - epoch_time).total_seconds()


def get_date_time(seconds_since_epoch):
    return datetime.fromtimestamp(seconds_since_epoch, timezone.utc)


def get_utc_now_seconds_since_epoch():
    return get_seconds_since_epoch(get_utc_now())


def unicode_to_utf8(data):
    """
    Convert unicode data in a collection to UTF-8 data. Used for supporting unicode config json strings on Python 2.7.
    Once Python 2.7 is no longer supported, this function can be removed.
    """
    if isinstance(data, dict):
        return {unicode_to_utf8(key): unicode_to_utf8(value) for key, value in data.iteritems()}
    elif isinstance(data, list):
        return [unicode_to_utf8(element) for element in data]
    elif isinstance(data, unicode):  # noqa: F821 (ignore warning: unicode is undefined in Python 3)
        return data.encode('utf-8')
    else:
        return data


def encode_utf8(value):
    """
    Get the UTF-8 encoded value of a string. Used for supporting unicode config json strings on Python 2.7.
    If the value is already UTF-8 encoded, it is returned as is.
    Once Python 2.7 is no longer supported, this function can be removed.
    The use of this function can be replaced with encode() method of the string: value.encode('utf-8')
    """
    try:
        return value.encode('utf-8')
    except UnicodeDecodeError:
        return value
