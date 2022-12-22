import sys
import inspect
from qualname import qualname
from datetime import datetime

epoch_time = datetime(1970, 1, 1)
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
    return datetime.utcnow()


def get_seconds_since_epoch(date_time):
    return (date_time - epoch_time).total_seconds()


def get_date_time(seconds_since_epoch):
    return datetime.utcfromtimestamp(seconds_since_epoch)


def get_utc_now_seconds_since_epoch():
    return get_seconds_since_epoch(get_utc_now())
