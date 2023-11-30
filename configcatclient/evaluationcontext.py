class EvaluationContext(object):
    def __init__(self,
                 key,
                 setting_type,
                 user,
                 visited_keys=None,
                 is_missing_user_object_logged=False,
                 is_missing_user_object_attribute_logged=False):
        self.key = key
        self.setting_type = setting_type
        self.user = user
        self.visited_keys = visited_keys
        self.is_missing_user_object_logged = is_missing_user_object_logged
        self.is_missing_user_object_attribute_logged = is_missing_user_object_attribute_logged
