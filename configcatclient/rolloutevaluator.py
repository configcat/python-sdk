import hashlib
import semver
import logging
import sys

from .user import User

log = logging.getLogger(sys.modules[__name__].__name__)


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

    VALUE = 'v'
    COMPARATOR = 't'
    COMPARISON_ATTRIBUTE = 'a'
    COMPARISON_VALUE = 'c'
    ROLLOUT_PERCENTAGE_ITEMS = 'p'
    PERCENTAGE = 'p'
    ROLLOUT_RULES = 'r'

    def evaluate(self, key, user, default_value, config):
        log.info('Evaluating get_value(\'%s\').' % key)

        setting_descriptor = config.get(key, None)

        if setting_descriptor is None:
            log.error('Evaluating get_value(\'%s\') failed. Value not found for key \'%s\' '
                      'Returning default_value: [%s]. Here are the available keys: %s' %
                      (key, key, str(default_value), ', '.join(list(config))))
            return default_value

        rollout_rules = setting_descriptor.get(self.ROLLOUT_RULES, [])
        rollout_percentage_items = setting_descriptor.get(self.ROLLOUT_PERCENTAGE_ITEMS, [])

        if user is not None and type(user) is not User:
            log.warning('Evaluating get_value(\'%s\'). User Object is not an instance of User type.' % key)
            user = None

        if user is None:
            if len(rollout_rules) > 0 or len(rollout_percentage_items) > 0:
                log.warning('Evaluating get_value(\'%s\'). UserObject missing! '
                            'You should pass a UserObject to get_value(), '
                            'in order to make targeting work properly. '
                            'Read more: https://configcat.com/docs/advanced/user-object/' %
                            key)
            return_value = setting_descriptor.get(self.VALUE, default_value)
            log.info('Returning [%s]' % str(return_value))
            return return_value

        log.info('User object:\n%s' % str(user))

        # Evaluate targeting rules
        for rollout_rule in rollout_rules:
            comparison_attribute = rollout_rule.get(self.COMPARISON_ATTRIBUTE)
            comparison_value = rollout_rule.get(self.COMPARISON_VALUE)
            comparator = rollout_rule.get(self.COMPARATOR)

            user_value = user.get_attribute(comparison_attribute)
            if user_value is None or not user_value:
                log.info(self._format_no_match_rule(comparison_attribute, user_value, comparator, comparison_value))
                continue

            value = rollout_rule.get(self.VALUE)

            # IS ONE OF
            if comparator == 0:
                if str(user_value) in [x.strip() for x in str(comparison_value).split(',')]:
                    log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                     comparison_value, value))
                    return value
            # IS NOT ONE OF
            elif comparator == 1:
                if str(user_value) not in [x.strip() for x in str(comparison_value).split(',')]:
                    log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                     comparison_value, value))
                    return value
            # CONTAINS
            elif comparator == 2:
                if str(user_value).__contains__(str(comparison_value)):
                    log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                     comparison_value, value))
                    return value
            # DOES NOT CONTAIN
            elif comparator == 3:
                if not str(user_value).__contains__(str(comparison_value)):
                    log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                     comparison_value, value))
                    return value

            # IS ONE OF, IS NOT ONE OF (Semantic version)
            elif 4 <= comparator <= 5:
                try:
                    match = False
                    for x in filter(None, [x.strip() for x in str(comparison_value).split(',')]):
                        match = semver.match(str(user_value).strip(), '==' + x) or match
                    if (match and comparator == 4) or (not match and comparator == 5):
                        log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                         comparison_value, value))
                        return value
                except ValueError as e:
                    log.warning(self._format_validation_error_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, str(e)))
                    continue

            # LESS THAN, LESS THAN OR EQUALS TO, GREATER THAN, GREATER THAN OR EQUALS TO (Semantic version)
            elif 6 <= comparator <= 9:
                try:
                    if semver.match(str(user_value).strip(),
                                    self.SEMANTIC_VERSION_COMPARATORS[comparator - 6] + str(comparison_value).strip()):
                        log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                         comparison_value, value))
                        return value
                except ValueError as e:
                    log.warning(self._format_validation_error_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, str(e)))
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
                        log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                         comparison_value, value))
                        return value
                except Exception as e:
                    log.warning(self._format_validation_error_rule(comparison_attribute, user_value, comparator,
                                                                   comparison_value, str(e)))
                    continue
            # IS ONE OF (Sensitive)
            elif comparator == 16:
                if str(hashlib.sha1(user_value.encode('utf8')).hexdigest()) in [x.strip() for x in str(comparison_value).split(',')]:
                    log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                     comparison_value, value))
                    return value
            # IS NOT ONE OF (Sensitive)
            elif comparator == 17:
                if str(hashlib.sha1(user_value.encode('utf8')).hexdigest()) not in [x.strip() for x in str(comparison_value).split(',')]:
                    log.info(self._format_match_rule(comparison_attribute, user_value, comparator,
                                                     comparison_value, value))
                    return value

            log.info(self._format_no_match_rule(comparison_attribute, user_value, comparator, comparison_value))

        # Evaluate variations
        if len(rollout_percentage_items) > 0:
            user_key = user.get_identifier()
            hash_candidate = ('%s%s' % (key, user_key)).encode('utf-8')
            hash_val = int(hashlib.sha1(hash_candidate).hexdigest()[:7], 16) % 100

            bucket = 0
            for rollout_percentage_item in rollout_percentage_items or []:
                bucket += rollout_percentage_item.get(self.PERCENTAGE, 0)
                if hash_val < bucket:
                    percentage_value = rollout_percentage_item.get(self.VALUE)
                    log.info('Evaluating %% options. Returning %s' % percentage_value)
                    return percentage_value

        def_value = setting_descriptor.get(self.VALUE, default_value)
        log.info('Returning %s' % def_value)
        return def_value

    def _format_match_rule(self, comparison_attribute, user_value, comparator, comparison_value, value):
        return 'Evaluating rule: [%s:%s] [%s] [%s] => match, returning: %s' \
               % (comparison_attribute, user_value, self.COMPARATOR_TEXTS[comparator], comparison_value, value)

    def _format_no_match_rule(self, comparison_attribute, user_value, comparator, comparison_value):
        return 'Evaluating rule: [%s:%s] [%s] [%s] => no match' \
               % (comparison_attribute, user_value, self.COMPARATOR_TEXTS[comparator], comparison_value)

    def _format_validation_error_rule(self, comparison_attribute, user_value, comparator, comparison_value, error):
        return 'Evaluating rule: [%s:%s] [%s] [%s] => SKIP rule. Validation error: %s' \
               % (comparison_attribute, user_value, self.COMPARATOR_TEXTS[comparator], comparison_value, error)
