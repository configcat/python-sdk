class EvaluationDetails(object):
    def __init__(self,
                 key,
                 value,
                 variation_id=None,
                 fetch_time=None,
                 user=None,
                 is_default_value=False,
                 error=None,
                 matched_evaluation_rule=None,
                 matched_evaluation_percentage_rule=None):
        self.key = key
        self.value = value
        self.variation_id = variation_id
        self.fetch_time = fetch_time
        self.user = user
        self.is_default_value = is_default_value
        self.error = error
        self.matched_evaluation_rule = matched_evaluation_rule
        self.matched_evaluation_percentage_rule = matched_evaluation_percentage_rule

    @staticmethod
    def from_error(key, value, error, variation_id=None):
        return EvaluationDetails(key=key, value=value, variation_id=variation_id, is_default_value=True, error=error)
