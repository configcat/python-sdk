import hashlib
import semver

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
        '>= (Number)'
    ]

    def __init__(self, logger):
        self._logger = logger

    def evaluate(self, key, user, default_value, config):
        self._logger.info('Evaluating get_value(\'%s\').' % key)

        setting_descriptor = config.get(key, None)

        if setting_descriptor is None:
            self._logger.error('Evaluating get_value(\'%s\') failed. Value not found for key \'%s\' '
                               'Returning default_value: [%s]. Here are the available keys: %s' %
                               (key, key, str(default_value), ', '.join(list(config))))
            return default_value

        rollout_rules = setting_descriptor.get('RolloutRules', [])
        rollout_percentage_items = setting_descriptor.get('RolloutPercentageItems', [])

        if user is not None and type(user) is not User:
            self._logger.warning('Evaluating get_value(\'%s\'). User Object is not an instance of User type.' % key)
            user = None

        if user is None:
            if len(rollout_rules) > 0 or len(rollout_percentage_items) > 0:
                self._logger.warning('Evaluating get_value(\'%s\'). UserObject missing! '
                                     'You should pass a UserObject to get_value(), '
                                     'in order to make targeting work properly. '
                                     'Read more: https://configcat.com/docs/advanced/user-object/' %
                                     key)
            return_value = setting_descriptor.get('Value', default_value)
            self._logger.info('Returning [%s]' % str(return_value))
            return return_value

        self._logger.info('User object:\n%s' % str(user))

        # Evaluate targeting rules
        for rollout_rule in rollout_rules:
            comparison_attribute = rollout_rule.get('ComparisonAttribute')
            comparison_value = rollout_rule.get('ComparisonValue')
            comparator = rollout_rule.get('Comparator')

            user_value = user.get_attribute(comparison_attribute)
            if user_value is None or not user_value:
                self._logger.info(self._format_no_match_rule(comparison_attribute, comparator, comparison_value))
                continue

            value = rollout_rule.get('Value')

            # IS ONE OF
            if comparator == 0:
                if str(user_value) in [x.strip() for x in str(comparison_value).split(',')]:
                    self._logger.info(self._format_match_rule(comparison_attribute, comparator, comparison_value,
                                                              value))
                    return value
            # IS NOT ONE OF
            elif comparator == 1:
                if str(user_value) not in [x.strip() for x in str(comparison_value).split(',')]:
                    self._logger.info(self._format_match_rule(comparison_attribute, comparator, comparison_value,
                                                              value))
                    return value
            # CONTAINS
            elif comparator == 2:
                if str(user_value).__contains__(str(comparison_value)):
                    self._logger.info(self._format_match_rule(comparison_attribute, comparator, comparison_value,
                                                              value))
                    return value
            # DOES NOT CONTAIN
            elif comparator == 3:
                if not str(user_value).__contains__(str(comparison_value)):
                    self._logger.info(self._format_match_rule(comparison_attribute, comparator, comparison_value,
                                                              value))
                    return value

            # IS ONE OF, IS NOT ONE OF (Semantic version)
            elif 4 <= comparator <= 5:
                try:
                    match = False
                    for x in filter(None, [x.strip() for x in str(comparison_value).split(',')]):
                        match = semver.match(str(user_value).strip(), '==' + x) or match
                    if (match and comparator == 4) or (not match and comparator == 5):
                        self._logger.info(self._format_match_rule(comparison_attribute, comparator, comparison_value,
                                                                  value))
                        return value
                except ValueError as e:
                    self._logger.warning(self._format_validation_error_rule(comparison_attribute, comparator,
                                                                            comparison_value, str(e)))
                    continue

            # LESS THAN, LESS THAN OR EQUALS TO, GREATER THAN, GREATER THAN OR EQUALS TO (Semantic version)
            elif 6 <= comparator <= 9:
                try:
                    if semver.match(str(user_value).strip(),
                                    self.SEMANTIC_VERSION_COMPARATORS[comparator - 6] + str(comparison_value).strip()):
                        self._logger.info(self._format_match_rule(comparison_attribute, comparator, comparison_value,
                                                                  value))
                        return value
                except ValueError as e:
                    self._logger.warning(self._format_validation_error_rule(comparison_attribute, comparator,
                                                                            comparison_value, str(e)))
                    continue

            self._logger.info(self._format_no_match_rule(comparison_attribute, comparator, comparison_value))

        # Evaluate variations
        if len(rollout_percentage_items) > 0:
            user_key = user.get_identifier()
            hash_candidate = ('%s%s' % (key, user_key)).encode('utf-8')
            hash_val = int(hashlib.sha1(hash_candidate).hexdigest()[:7], 16) % 100

            bucket = 0
            for rollout_percentage_item in rollout_percentage_items or []:
                bucket += rollout_percentage_item.get('Percentage', 0)
                if hash_val < bucket:
                    percentage_value = rollout_percentage_item.get('Value')
                    self._logger.info('Evaluating %% options. Returning %s' % percentage_value)
                    return percentage_value

        def_value = setting_descriptor.get('Value', default_value)
        self._logger.info('Returning %s' % def_value)
        return def_value

    def _format_match_rule(self, comparison_attribute, comparator, comparison_value, value):
        return 'Evaluating rule: [%s] [%s] [%s] => match, returning: %s' \
               % (comparison_attribute, self.COMPARATOR_TEXTS[comparator], comparison_value, value)

    def _format_no_match_rule(self, comparison_attribute, comparator, comparison_value):
        return 'Evaluating rule: [%s] [%s] [%s] => no match' \
               % (comparison_attribute, self.COMPARATOR_TEXTS[comparator], comparison_value)

    def _format_validation_error_rule(self, comparison_attribute, comparator, comparison_value, error):
        return 'Evaluating rule: [%s] [%s] [%s] => SKIP rule. Validation error: %s' \
               % (comparison_attribute, self.COMPARATOR_TEXTS[comparator], comparison_value, error)
