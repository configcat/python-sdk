import hashlib
import logging
import sys
import semver

from .user import User

log = logging.getLogger(sys.modules[__name__].__name__)


class RolloutEvaluator(object):

    @staticmethod
    def evaluate(key, user, default_value, config):
        if user is not None and type(user) is not User:
            log.warning("User parameter is not an instance of User type.")
            user = None

        setting_descriptor = config.get(key, None)

        if setting_descriptor is None:
            log.warning("Could not find setting by key, returning default value. Key: [%s]", key)
            return default_value

        if user is None:
            return setting_descriptor.get('Value', default_value)

        # Evaluate targeting rules
        rollout_rules = setting_descriptor.get('RolloutRules', [])
        for rollout_rule in rollout_rules:
            comparison_attribute = rollout_rule.get('ComparisonAttribute')
            user_value = user.get_attribute(comparison_attribute)
            if user_value is None or not user_value:
                continue

            comparison_value = rollout_rule.get('ComparisonValue')
            comparator = rollout_rule.get('Comparator')
            value = rollout_rule.get('Value')

            # IS ONE OF
            if comparator == 0:
                if str(user_value) in [x.strip() for x in str(comparison_value).split(',')]:
                    return value
            # IS NOT ONE OF
            elif comparator == 1:
                if str(user_value) not in [x.strip() for x in str(comparison_value).split(',')]:
                    return value
            # CONTAINS
            elif comparator == 2:
                if str(user_value).__contains__(str(comparison_value)):
                    return value
            # DOES NOT CONTAIN
            elif comparator == 3:
                if not str(user_value).__contains__(str(comparison_value)):
                    return value

            # IS ONE OF, IS NOT ONE OF (Semantic version)
            elif 4 <= comparator <= 5:
                try:
                    match = False
                    for x in filter(None, [x.strip() for x in str(comparison_value).split(',')]):
                        match = semver.match(str(user_value).strip(), '==' + x) or match
                    if (match and comparator == 4) or (not match and comparator == 5):
                        return value
                except ValueError as e:
                    # If any of the
                    # TODO logging
                    pass

            # LESS THAN, LESS THAN OR EQUALS TO, GREATER THAN, GREATER THAN OR EQUALS TO (Semantic version)
            elif 6 <= comparator <= 9:
                try:
                    comparators = ['<', '<=', '>', '>=']
                    if semver.match(str(user_value).strip(), comparators[comparator - 6] + str(comparison_value).strip()):
                        return value
                except ValueError as e:
                    # If any of the
                    # TODO logging
                    pass

        # Evaluate variations
        rollout_percentage_items = setting_descriptor.get('RolloutPercentageItems', [])
        if len(rollout_percentage_items) > 0:
            user_key = user.get_identifier()
            hash_candidate = ('%s%s' % (key, user_key)).encode('utf-8')
            hash_val = int(hashlib.sha1(hash_candidate).hexdigest()[:7], 16) % 100

            bucket = 0
            for rollout_percentage_item in rollout_percentage_items or []:
                bucket += rollout_percentage_item.get('Percentage', 0)
                if hash_val < bucket:
                    return rollout_percentage_item.get('Value')

        return setting_descriptor.get('Value', default_value)
