class EvaluationDetails(object):
    def __init__(self,
                 key,
                 value,
                 variation_id=None,
                 fetch_time=None,
                 user=None,
                 is_default_value=False,
                 error=None,
                 matched_targeting_rule=None,
                 matched_percentage_option=None):
        # Key of the feature flag or setting.
        self.key = key

        # Evaluated value of the feature flag or setting.
        self.value = value

        # Variation ID of the feature flag or setting (if available).
        self.variation_id = variation_id

        # Time of last successful config download.
        self.fetch_time = fetch_time

        # The User Object used for the evaluation (if available).
        self.user = user

        # Indicates whether the default value passed to the setting evaluation methods like ConfigCatClient.get_value,
        # ConfigCatClient.get_value_details, etc. is used as the result of the evaluation.
        self.is_default_value = is_default_value

        # Error message in case evaluation failed.
        self.error = error

        # The targeting rule (if any) that matched during the evaluation and was used to return the evaluated value.
        self.matched_targeting_rule = matched_targeting_rule

        # The percentage option (if any) that was used to select the evaluated value.
        self.matched_percentage_option = matched_percentage_option

    @staticmethod
    def from_error(key, value, error, variation_id=None):
        return EvaluationDetails(key=key, value=value, variation_id=variation_id, is_default_value=True, error=error)
