import hashlib
import semver

from .logger import Logger

from .constants import ROLLOUT_RULES, ROLLOUT_PERCENTAGE_ITEMS, VALUE, VARIATION_ID, COMPARISON_ATTRIBUTE, \
    COMPARISON_VALUE, COMPARATOR, PERCENTAGE
from .user import User


class RolloutEvaluator(object):
    SEMANTIC_VERSION_COMPARATORS = ['<', '<=', '>', '>=']
    COMPARATOR_TEXTS = [
        'IS ONE OF',
        'IS NOT ONE OF',
        'CONTAINS',
        'DOES NOT CONTAIN',
        'IS ONE OF (SemVer)',
        'IS NOT ONE OF (SemVer)',
        '< (SemVer)',
        '<= (SemVer)',
        '> (SemVer)',
        '>= (SemVer)',
        '= (Number)',
        '<> (Number)',
        '< (Number)',
        '<= (Number)',
        '> (Number)',
        '>= (Number)',
        'IS ONE OF (Sensitive)',
        'IS NOT ONE OF (Sensitive)'
    ]

    def __init__(self, log):
        self.log = log

    def evaluate(self, key, user, default_value, default_variation_id, settings):  # noqa: C901
        """
        returns value, variation_id, matched_evaluation_rule, matched_evaluation_percentage_rule, error
        """
        setting_descriptor = settings.get(key)

        if setting_descriptor is None:
            error = 'Failed to evaluate setting \'%s\' (the key was not found in config JSON). ' \
                    'Returning the `%s` parameter that you specified in your application: \'%s\'. ' \
                    'Available keys: [%s].'
            error_args = (key, 'default_value', str(default_value), ', '.join("'{}'".format(s) for s in list(settings)))
            self.log.error(error, *error_args, event_id=1001)
            return default_value, default_variation_id, None, None, Logger.format(error, error_args)

        rollout_rules = setting_descriptor.get(ROLLOUT_RULES, [])
        rollout_percentage_items = setting_descriptor.get(ROLLOUT_PERCENTAGE_ITEMS, [])

        user_has_invalid_type = user is not None and type(user) is not User
        if user_has_invalid_type:
            self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                             '(User Object is not an instance of User type).',
                             key, event_id=4001)
            user = None

        if user is None:
            if not user_has_invalid_type and (len(rollout_rules) > 0 or len(rollout_percentage_items) > 0):
                self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                                 '(User Object is missing). '
                                 'You should pass a User Object to the evaluation methods like `get_value()` '
                                 'in order to make targeting work properly. '
                                 'Read more: https://configcat.com/docs/advanced/user-object/',
                                 key, event_id=3001)
            return_value = setting_descriptor.get(VALUE, default_value)
            return_variation_id = setting_descriptor.get(VARIATION_ID, default_variation_id)
            self.log.info('%s', 'Returning [%s]' % str(return_value), event_id=5000)
            return return_value, return_variation_id, None, None, None

        log_entries = ['Evaluating get_value(\'%s\').' % key, 'User object:\n%s' % str(user)]

        try:
            # Evaluate targeting rules
            for rollout_rule in rollout_rules:
                comparison_attribute = rollout_rule.get(COMPARISON_ATTRIBUTE)
                comparison_value = rollout_rule.get(COMPARISON_VALUE)
                comparator = rollout_rule.get(COMPARATOR)

                user_value = user.get_attribute(comparison_attribute)
                if user_value is None or not user_value:
                    log_entries.append(
                        self._format_no_match_rule(comparison_attribute, user_value, comparator, comparison_value)
                    )
                    continue

                value = rollout_rule.get(VALUE)
                variation_id = rollout_rule.get(VARIATION_ID, default_variation_id)

                # IS ONE OF
                if comparator == 0:
                    if str(user_value) in [x.strip() for x in str(comparison_value).split(',')]:
                        log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, value))
                        return value, variation_id, rollout_rule, None, None
                # IS NOT ONE OF
                elif comparator == 1:
                    if str(user_value) not in [x.strip() for x in str(comparison_value).split(',')]:
                        log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, value))
                        return value, variation_id, rollout_rule, None, None
                # CONTAINS
                elif comparator == 2:
                    if str(user_value).__contains__(str(comparison_value)):
                        log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, value))
                        return value, variation_id, rollout_rule, None, None
                # DOES NOT CONTAIN
                elif comparator == 3:
                    if not str(user_value).__contains__(str(comparison_value)):
                        log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, value))
                        return value, variation_id, rollout_rule, None, None

                # IS ONE OF, IS NOT ONE OF (Semantic version)
                elif 4 <= comparator <= 5:
                    try:
                        match = False
                        for x in filter(None, [x.strip() for x in str(comparison_value).split(',')]):
                            match = semver.VersionInfo.parse(str(user_value).strip()).match('==' + x) or match
                        if (match and comparator == 4) or (not match and comparator == 5):
                            log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                       comparison_value, value))
                            return value, variation_id, rollout_rule, None, None
                    except ValueError as e:
                        message = self._format_validation_error_rule(comparison_attribute, user_value, comparator,
                                                                     comparison_value, str(e))
                        self.log.warning(message)
                        log_entries.append(message)
                        continue

                # LESS THAN, LESS THAN OR EQUALS TO, GREATER THAN, GREATER THAN OR EQUALS TO (Semantic version)
                elif 6 <= comparator <= 9:
                    try:
                        if semver.VersionInfo.parse(str(user_value).strip()).match(
                            self.SEMANTIC_VERSION_COMPARATORS[comparator - 6] + str(comparison_value).strip()
                        ):
                            log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                       comparison_value, value))
                            return value, variation_id, rollout_rule, None, None
                    except ValueError as e:
                        message = self._format_validation_error_rule(comparison_attribute, user_value, comparator,
                                                                     comparison_value, str(e))
                        self.log.warning(message)
                        log_entries.append(message)
                        continue
                elif 10 <= comparator <= 15:
                    try:
                        user_value_float = float(str(user_value).replace(",", "."))
                        comparison_value_float = float(str(comparison_value).replace(",", "."))

                        if (comparator == 10 and user_value_float == comparison_value_float) \
                                or (comparator == 11 and user_value_float != comparison_value_float) \
                                or (comparator == 12 and user_value_float < comparison_value_float) \
                                or (comparator == 13 and user_value_float <= comparison_value_float) \
                                or (comparator == 14 and user_value_float > comparison_value_float) \
                                or (comparator == 15 and user_value_float >= comparison_value_float):
                            log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                       comparison_value, value))
                            return value, variation_id, rollout_rule, None, None
                    except Exception as e:
                        message = self._format_validation_error_rule(comparison_attribute, user_value, comparator,
                                                                     comparison_value, str(e))
                        self.log.warning(message)
                        log_entries.append(message)
                        continue
                # IS ONE OF (Sensitive)
                elif comparator == 16:
                    if str(hashlib.sha1(user_value.encode('utf8')).hexdigest()) in [  # NOSONAR python:S4790
                        x.strip() for x in str(comparison_value).split(',')
                    ]:
                        log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, value))
                        return value, variation_id, rollout_rule, None, None
                # IS NOT ONE OF (Sensitive)
                elif comparator == 17:
                    if str(hashlib.sha1(user_value.encode('utf8')).hexdigest()) not in [  # NOSONAR python:S4790
                        x.strip() for x in str(comparison_value).split(',')
                    ]:
                        log_entries.append(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, value))
                        return value, variation_id, rollout_rule, None, None

                log_entries.append(self._format_no_match_rule(comparison_attribute, user_value, comparator, comparison_value))

            # Evaluate variations
            if len(rollout_percentage_items) > 0:
                user_key = user.get_identifier()
                hash_candidate = ('%s%s' % (key, user_key)).encode('utf-8')
                hash_val = int(hashlib.sha1(hash_candidate).hexdigest()[:7], 16) % 100

                bucket = 0
                for rollout_percentage_item in rollout_percentage_items or []:
                    bucket += rollout_percentage_item.get(PERCENTAGE, 0)
                    if hash_val < bucket:
                        percentage_value = rollout_percentage_item.get(VALUE)
                        variation_id = rollout_percentage_item.get(VARIATION_ID, default_variation_id)
                        log_entries.append('Evaluating %% options. Returning %s' % percentage_value)
                        return percentage_value, variation_id, None, rollout_percentage_item, None

            return_value = setting_descriptor.get(VALUE, default_value)
            return_variation_id = setting_descriptor.get(VARIATION_ID, default_variation_id)
            log_entries.append('Returning %s' % return_value)
            return return_value, return_variation_id, None, None, None
        finally:
            self.log.info('%s', '\n'.join(log_entries), event_id=5000)

    def _format_match_rule(self, comparison_attribute, user_value, comparator, comparison_value, value):
        return 'Evaluating rule: [%s:%s] [%s] [%s] => match, returning: %s' \
               % (comparison_attribute, user_value, self.COMPARATOR_TEXTS[comparator], comparison_value, value)

    def _format_no_match_rule(self, comparison_attribute, user_value, comparator, comparison_value):
        return 'Evaluating rule: [%s:%s] [%s] [%s] => no match' \
               % (comparison_attribute, user_value, self.COMPARATOR_TEXTS[comparator], comparison_value)

    def _format_validation_error_rule(self, comparison_attribute, user_value, comparator, comparison_value, error):
        return 'Evaluating rule: [%s:%s] [%s] [%s] => SKIP rule. Validation error: %s' \
               % (comparison_attribute, user_value, self.COMPARATOR_TEXTS[comparator], comparison_value, error)
