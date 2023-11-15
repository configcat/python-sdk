class EvaluationContext(object):
    def __init__(self,
                 key,
                 user,
                 visited_keys=None,
                 is_missing_user_object_logged=False,
                 is_missing_user_object_attribute_logged=False,
                 type_mismatched_logged_user_attributes=None):
        self.key = key
        self.user = user
        self.visited_keys = visited_keys
        self.is_missing_user_object_logged = is_missing_user_object_logged
        self.is_missing_user_object_attribute_logged = is_missing_user_object_attribute_logged
        self.type_mismatched_logged_user_attributes = type_mismatched_logged_user_attributes or []
