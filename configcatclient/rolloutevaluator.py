from enum import IntEnum

import hashlib
import semver

from .logger import Logger

from .constants import TARGETING_RULES, VALUE, VARIATION_ID, COMPARISON_ATTRIBUTE, \
    COMPARATOR, PERCENTAGE, SERVED_VALUE, CONDITIONS, PERCENTAGE_OPTIONS, PERCENTAGE_RULE_ATTRIBUTE, \
    COMPARISON_RULE, STRING_LIST_VALUE, DOUBLE_VALUE, STRING_VALUE, FEATURE_FLAGS, PREFERENCES, SALT, SEGMENTS, \
    SEGMENT_CONDITION, PREREQUISITE_FLAG_CONDITION, SEGMENT_INDEX, SEGMENT_COMPARATOR, SEGMENT_RULES, SEGMENT_NAME, \
    PREREQUISITE_FLAG_KEY, PREREQUISITE_COMPARATOR, BOOL_VALUE, INT_VALUE
from .user import User


def sha256(value, salt, context_salt):
    """
    Calculates the SHA256 hash of the given value with the given salt and context_salt.
    """
    return hashlib.sha256(value.encode('utf8') + salt.encode('utf8') + context_salt.encode('utf8')).hexdigest()


def get_value(dictionary):
    value = dictionary.get(VALUE)
    if value is None:
        raise ValueError('Value is missing.')

    if value.get(BOOL_VALUE) is not None:
        return value.get(BOOL_VALUE)
    if value.get(STRING_VALUE) is not None:
        return value.get(STRING_VALUE)
    if value.get(INT_VALUE) is not None:
        return value.get(INT_VALUE)
    if value.get(DOUBLE_VALUE) is not None:
        return value.get(DOUBLE_VALUE)

    raise ValueError('Unknown value type.')


class SegmentComparator(IntEnum):
    IS_IN = 0
    IS_NOT_IN = 1


class RolloutEvaluator(object):
    SEMANTIC_VERSION_COMPARATORS = ['<', '<=', '>', '>=']
    COMPARATOR_TEXTS = [
        'IS ONE OF',
        'IS NOT ONE OF',
        'CONTAINS ANY OF',
        'NOT CONTAINS ANY OF',
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
        'IS ONE OF (hashed)',
        'IS NOT ONE OF (hashed)',
        'BEFORE (UTC DateTime)',
        'AFTER (UTC DateTime)',
        'EQUALS (hashed)',
        'NOT EQUALS (hashed)',
        'STARTS WITH ANY OF (hashed)',
        'ENDS WITH (hashed)',
        'ARRAY CONTAINS (hashed)',
        'ARRAY NOT CONTAINS (hashed)'
    ]
    COMPARISON_VALUES = [
        STRING_LIST_VALUE,  # IS ONE OF
        STRING_LIST_VALUE,  # IS NOT ONE OF
        STRING_LIST_VALUE,  # CONTAINS ANY OF
        STRING_LIST_VALUE,  # NOT CONTAINS ANY OF
        STRING_LIST_VALUE,  # IS ONE OF (SemVer)
        STRING_LIST_VALUE,  # IS NOT ONE OF (SemVer)
        STRING_VALUE,       # < (SemVer)
        STRING_VALUE,       # <= (SemVer)
        STRING_VALUE,       # > (SemVer)
        STRING_VALUE,       # >= (SemVer)
        DOUBLE_VALUE,       # = (Number)
        DOUBLE_VALUE,       # <> (Number)
        DOUBLE_VALUE,       # < (Number)
        DOUBLE_VALUE,       # <= (Number)
        DOUBLE_VALUE,       # > (Number)
        DOUBLE_VALUE,       # >= (Number)
        STRING_LIST_VALUE,  # IS ONE OF (hashed)
        STRING_LIST_VALUE,  # IS NOT ONE OF (hashed)
        DOUBLE_VALUE,       # BEFORE (UTC DateTime)
        DOUBLE_VALUE,       # AFTER (UTC DateTime)
        STRING_VALUE,       # EQUALS (hashed)
        STRING_VALUE,       # NOT EQUALS (hashed)
        STRING_LIST_VALUE,  # STARTS WITH ANY OF (hashed)
        STRING_LIST_VALUE,  # ENDS WITH (hashed)
        STRING_VALUE,       # ARRAY CONTAINS (hashed)
        STRING_VALUE        # ARRAY NOT CONTAINS (hashed)
    ]
    SEGMENT_COMPARATOR_TEXTS = ['IS IN SEGMENT', 'IS NOT IN SEGMENT']
    PREREQUISITE_COMPARATOR_TEXTS = ['EQUALS', 'DOES NOT EQUAL']

    def __init__(self, log):
        self.log = log

    def evaluate(self, key, user, default_value, default_variation_id, config, log_builder, visited_keys=None):  # noqa: C901
        """
        returns value, variation_id, matched_evaluation_rule, matched_evaluation_percentage_rule, error
        """

        # Circular dependency check
        if visited_keys is None:
            visited_keys = []
        if key in visited_keys:
            error = 'Cannot evaluate targeting rules for \'%s\' (circular dependency detected between the following ' \
                    'depending flags: %s). Please check your feature flag definition and eliminate the circular dependency.'
            error_args = (key, ' -> '.join("'{}'".format(s) for s in list(visited_keys) + [key]))
            self.log.error(error, *error_args, event_id=2003)
            return default_value, default_variation_id, None, None, Logger.format(error, error_args)
        visited_keys.append(key)
        is_root_flag_evaluation = len(visited_keys) == 1

        settings = config.get(FEATURE_FLAGS, {})
        salt = config.get(PREFERENCES, {}).get(SALT, '')
        setting_descriptor = settings.get(key)

        if setting_descriptor is None:
            error = 'Failed to evaluate setting \'%s\' (the key was not found in config JSON). ' \
                    'Returning the `%s` parameter that you specified in your application: \'%s\'. ' \
                    'Available keys: [%s].'
            error_args = (key, 'default_value', str(default_value), ', '.join("'{}'".format(s) for s in list(settings)))
            self.log.error(error, *error_args, event_id=1001)
            return default_value, default_variation_id, None, None, Logger.format(error, error_args)

        targeting_rules = setting_descriptor.get(TARGETING_RULES, [])
        percentage_rule_attribute = setting_descriptor.get(PERCENTAGE_RULE_ATTRIBUTE)

        # TODO: How to handle this case in evaluation logging?
        user_has_invalid_type = user is not None and not isinstance(user, User)
        if user_has_invalid_type:
            self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                             '(User Object is not an instance of User type).',
                             key, event_id=4001)
            user = None

        try:
            if log_builder and is_root_flag_evaluation:
                log_builder.append("Evaluating '{}'".format(key) + (" for User '{}'".format(user) if user is not None else ''))
                log_builder.increase_indent()

            # Evaluate targeting rules (logically connected by OR)
            has_conditions = False
            for targeting_rule in targeting_rules:
                conditions = targeting_rule.get(CONDITIONS, [])
                percentage_options = targeting_rule.get(PERCENTAGE_OPTIONS, [])

                if len(conditions) > 0:
                    if not has_conditions:
                        log_builder and log_builder.new_line('Evaluating targeting rules and applying the first match if any:')
                        has_conditions = True

                    served_value = targeting_rule.get(SERVED_VALUE)
                    value = get_value(served_value) if served_value is not None else None

                    # Evaluate targeting rule conditions (logically connected by AND)
                    if self.evaluate_conditions(conditions, user, key, salt, config, log_builder, visited_keys, value):
                        served_value = targeting_rule.get(SERVED_VALUE)
                        if served_value is not None:
                            variation_id = served_value.get(VARIATION_ID, default_variation_id)
                            log_builder and is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % value)
                            return value, variation_id, targeting_rule, None, None
                    else:
                        continue

                # Evaluate variations
                if len(percentage_options) > 0:
                    if len(conditions) > 0 and log_builder:
                        log_builder.increase_indent()

                    if user is None:
                        self.log.warning('Cannot evaluate %% options for setting \'%s\' '
                                         '(User Object is missing). '
                                         'You should pass a User Object to the evaluation methods like `get_value()` '
                                         'in order to make targeting work properly. '
                                         'Read more: https://configcat.com/docs/advanced/user-object/',
                                         key, event_id=3001)

                        if log_builder:
                            log_builder.new_line('Skipping % options because the User Object is missing.')
                            if len(conditions) > 0:
                                log_builder.decrease_indent()
                        continue

                    user_attribute_name = percentage_rule_attribute if percentage_rule_attribute is not None else 'Identifier'
                    user_key = user.get_attribute(percentage_rule_attribute) if percentage_rule_attribute is not None \
                        else user.get_identifier()
                    if percentage_rule_attribute is not None and user_key is None:
                        if log_builder:
                            log_builder.new_line(
                                'Skipping %% options because the User.%s attribute is missing.' % user_attribute_name)
                            log_builder.new_line(
                                'The current targeting rule is ignored and the evaluation continues with the next rule.')
                            if len(conditions) > 0:
                                log_builder.decrease_indent()
                        continue

                    hash_candidate = ('%s%s' % (key, user_key)).encode('utf-8')
                    hash_val = int(hashlib.sha1(hash_candidate).hexdigest()[:7], 16) % 100

                    bucket = 0
                    index = 1
                    for percentage_option in percentage_options or []:
                        bucket += percentage_option.get(PERCENTAGE, 0)
                        if hash_val < bucket:
                            percentage_value = get_value(percentage_option)
                            variation_id = percentage_option.get(VARIATION_ID, default_variation_id)
                            if log_builder:
                                log_builder.new_line('Evaluating %% options based on the User.%s attribute:' %
                                                     user_attribute_name)
                                log_builder.new_line('- Computing hash in the [0..99] range from User.%s => %s '
                                                     '(this value is sticky and consistent across all SDKs)' %
                                                     (user_attribute_name, hash_val))
                                log_builder.new_line("- Hash value %s selects %% option %s (%s%%), '%s'" %
                                                     (hash_val, index, bucket, percentage_value))
                                if len(conditions) > 0:
                                    log_builder.decrease_indent()
                                is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % percentage_value)
                            return percentage_value, variation_id, None, percentage_option, None
                        index += 1

            return_value = get_value(setting_descriptor)
            return_variation_id = setting_descriptor.get(VARIATION_ID, default_variation_id)
            log_builder and is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % return_value)
            return return_value, return_variation_id, None, None, None
        except Exception as e:
            error = 'Failed to evaluate setting \'%s\'. (%s)' \
                    'Returning the `%s` parameter that you specified in your application: \'%s\'. '
            error_args = (key, str(e), 'default_value', str(default_value))
            self.log.error(error, *error_args, event_id=2001)
            return default_value, default_variation_id, None, None, Logger.format(error, error_args)

    def _trunc_if_needed(self, comparator, comparison_value):
        if '(hashed)' in self.COMPARATOR_TEXTS[comparator]:
            if isinstance(comparison_value, list):
                return [item[:10] + '...' for item in comparison_value]

            return comparison_value[:10] + '...'

        return comparison_value

    def _format_rule(self, comparison_attribute, comparator, comparison_value):
        return 'User.%s %s %s ' \
               % (comparison_attribute, self.COMPARATOR_TEXTS[comparator],
                  self._trunc_if_needed(comparator, comparison_value))

    def _format_error_rule(self, comparison_attribute, comparator, comparison_value, error):
        return 'Evaluating rule: User.%s %s %s => SKIP rule. %s' \
               % (comparison_attribute, self.COMPARATOR_TEXTS[comparator],
                  self._trunc_if_needed(comparator, comparison_value), error)

    def evaluate_conditions(self, conditions, user, key, salt, config, log_builder, visited_keys, value):  # noqa: C901
        segments = config.get(SEGMENTS, [])

        first_condition = True
        condition_result = True
        error = None
        for condition in conditions:
            comparison_rule = condition.get(COMPARISON_RULE)
            segment_condition = condition.get(SEGMENT_CONDITION)
            prerequisite_flag_condition = condition.get(PREREQUISITE_FLAG_CONDITION)

            if first_condition:
                if log_builder:
                    log_builder.new_line('- IF ')
                    log_builder.increase_indent()
                first_condition = False
            else:
                if log_builder:
                    log_builder.new_line('AND ')

            if comparison_rule is not None:
                result, error = self._evaluate_comparison_rule_condition(comparison_rule, user, key, key, salt, log_builder)
                if log_builder and len(conditions) > 1:
                    log_builder.append('=> {}'.format(result))
                    if not result:
                        log_builder.append(', skipping the remaining AND conditions')

                if not result:
                    condition_result = False
                    break
            elif segment_condition is not None:
                result, error = self._evaluate_segment_condition(segment_condition, user, key, salt, segments, log_builder)
                if log_builder:
                    if len(conditions) > 1:
                        log_builder.append(' => {}'.format(result))
                        if not result:
                            log_builder.append(', skipping the remaining AND conditions')
                    elif error is None:
                        log_builder.new_line()

                if not result:
                    condition_result = False
                    break
            elif prerequisite_flag_condition is not None:
                result, error = self._evaluate_prerequisite_flag_condition(prerequisite_flag_condition, user, config,
                                                                           log_builder, visited_keys)
                if not result:
                    condition_result = False
                    break

        if log_builder:
            if len(conditions) > 1:
                log_builder.new_line()
            if error:
                log_builder.append('THEN %s => %s' % (
                    "'" + str(value) + "'" if value is not None else '% options',
                    error))
                log_builder.new_line(
                    'The current targeting rule is ignored and the evaluation continues with the next rule.')
            else:
                log_builder.append('THEN %s => %s' % (
                    "'" + str(value) + "'" if value is not None else '% options',
                    'MATCH, applying rule' if condition_result else 'no match'))
            if len(conditions) > 0:
                log_builder.decrease_indent()

        return condition_result

    def _evaluate_prerequisite_flag_condition(self, prerequisite_flag_condition, user, config, log_builder, visited_keys):  # noqa: C901, E501
        prerequisite_key = prerequisite_flag_condition.get(PREREQUISITE_FLAG_KEY)
        prerequisite_comparator = prerequisite_flag_condition.get(PREREQUISITE_COMPARATOR)

        prerequisite_condition_result = False
        try:
            prerequisite_comparison_value = get_value(prerequisite_flag_condition)
        except ValueError as e:
            log_builder and log_builder.new_line('Prerequisite comparison value error: %s' % str(e))
            return prerequisite_condition_result, None

        if log_builder:
            log_builder.append("flag '%s' %s '%s'" %
                               (prerequisite_key, self.PREREQUISITE_COMPARATOR_TEXTS[prerequisite_comparator],
                                str(prerequisite_comparison_value)))
            log_builder.new_line('(').increase_indent()
            log_builder.new_line("Evaluating prerequisite flag '%s':" % prerequisite_key)

        prerequisite_value, _, _, _, error = self.evaluate(prerequisite_key, user, None, None, config,
                                                           log_builder, visited_keys)
        if error is not None:
            return prerequisite_condition_result, error

        if log_builder:
            log_builder.new_line("Prerequisite flag evaluation result: '%s'" % str(prerequisite_value))
            log_builder.new_line("Condition: (Flag '%s' %s '%s') evaluates to " %
                                 (prerequisite_key, self.PREREQUISITE_COMPARATOR_TEXTS[prerequisite_comparator],
                                  str(prerequisite_comparison_value)))

        # EQUALS
        if prerequisite_comparator == 0:
            if prerequisite_value == prerequisite_comparison_value:
                prerequisite_condition_result = True
        # DOES NOT EQUAL
        elif prerequisite_comparator == 1:
            if prerequisite_value != prerequisite_comparison_value:
                prerequisite_condition_result = True

        if log_builder:
            log_builder.append('%s.' % prerequisite_condition_result)
            log_builder.decrease_indent().new_line(')').new_line()

        return prerequisite_condition_result, None

    def _evaluate_segment_condition(self, segment_condition, user, key, salt, segments, log_builder):  # noqa: C901
        segment_index = segment_condition.get(SEGMENT_INDEX)
        segment = segments[segment_index]
        segment_name = segment.get(SEGMENT_NAME, '')
        segment_comparator = segment_condition.get(SEGMENT_COMPARATOR)
        segment_comparison_rules = segment.get(SEGMENT_RULES, [])

        if user is None:
            self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                             '(User Object is missing). '
                             'You should pass a User Object to the evaluation methods like `get_value()` '
                             'in order to make targeting work properly. '
                             'Read more: https://configcat.com/docs/advanced/user-object/',
                             key, event_id=3001)
            if log_builder:
                log_builder.append("User %s '%s' " % (self.SEGMENT_COMPARATOR_TEXTS[segment_comparator], segment_name))
            return False, 'cannot evaluate, User Object is missing'

        # IS IN SEGMENT, IS NOT IN SEGMENT
        if segment_comparator in [SegmentComparator.IS_IN, SegmentComparator.IS_NOT_IN]:
            if log_builder:
                log_builder.append("User %s '%s'" %
                                   (self.SEGMENT_COMPARATOR_TEXTS[segment_comparator], segment_name))
                log_builder.new_line('(').increase_indent()
                log_builder.new_line("Evaluating segment '%s':" % segment_name)

            # Set initial condition result based on comparator
            segment_condition_result = segment_comparator == SegmentComparator.IS_IN

            # Evaluate segment rules (logically connected by AND)
            first_segment_rule = True
            error = None
            for segment_comparison_rule in segment_comparison_rules:
                if first_segment_rule:
                    if log_builder:
                        log_builder.new_line('- IF ')
                        log_builder.increase_indent()
                    first_segment_rule = False
                else:
                    if log_builder:
                        log_builder.new_line('AND ')

                result, error = self._evaluate_comparison_rule_condition(segment_comparison_rule, user, key,
                                                                         segment_name, salt, log_builder)
                if log_builder:
                    log_builder.append('=> {}'.format(result))
                    if not result:
                        log_builder.append(', skipping the remaining AND conditions')

                if not result:
                    segment_condition_result = False if segment_comparator == SegmentComparator.IS_IN else True
                    break

            if log_builder:
                log_builder.decrease_indent()
                segment_evaluation_result = segment_condition_result if segment_comparator == SegmentComparator.IS_IN \
                    else not segment_condition_result
                log_builder.new_line('Segment evaluation result: User IS%sIN SEGMENT.' %
                                     (' ' if segment_evaluation_result else ' NOT '))
                log_builder.new_line("Condition (User %s '%s') evaluates to %s." %
                                     (self.SEGMENT_COMPARATOR_TEXTS[segment_comparator],
                                      segment_name, segment_condition_result))
                log_builder.decrease_indent().new_line(')')
            return segment_condition_result, error

        return False, None

    def _evaluate_comparison_rule_condition(self, comparison_rule, user, key, context_salt, salt, log_builder):  # noqa: C901, E501
        """
        returns result of comparison rule condition, error
        """

        comparison_attribute = comparison_rule.get(COMPARISON_ATTRIBUTE)
        comparator = comparison_rule.get(COMPARATOR)
        comparison_value = comparison_rule.get(self.COMPARISON_VALUES[comparator])
        error = None

        if log_builder:
            log_builder.append(self._format_rule(comparison_attribute, comparator, comparison_value))

        if user is None:
            self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                             '(User Object is missing). '
                             'You should pass a User Object to the evaluation methods like `get_value()` '
                             'in order to make targeting work properly. '
                             'Read more: https://configcat.com/docs/advanced/user-object/',
                             key, event_id=3001)
            error = 'cannot evaluate, User Object is missing'
            return False, error

        user_value = user.get_attribute(comparison_attribute)
        if user_value is None or not user_value:
            # TODO: Should we handle this as an error/warning?
            return False, error

        # IS ONE OF
        if comparator == 0:
            if str(user_value) in [x.strip() for x in comparison_value]:
                return True, error
        # IS NOT ONE OF
        elif comparator == 1:
            if str(user_value) not in [x.strip() for x in comparison_value]:
                return True, error
        # CONTAINS ANY OF
        elif comparator == 2:
            for comparison in comparison_value:
                if str(comparison) in str(user_value):
                    return True, error
        # NOT CONTAINS ANY OF
        elif comparator == 3:
            if not any(str(comparison) in str(user_value) for comparison in comparison_value):
                return True, error
        # IS ONE OF, IS NOT ONE OF (Semantic version)
        elif 4 <= comparator <= 5:
            try:
                match = False
                for x in filter(None, [x.strip() for x in comparison_value]):
                    match = semver.VersionInfo.parse(str(user_value).strip()).match('==' + x) or match
                if (match and comparator == 4) or (not match and comparator == 5):
                    return True, error
            except ValueError as e:
                # TODO: how to handle this?
                error = 'Validation error: ' + str(e)
                message = self._format_error_rule(comparison_attribute, comparator,
                                                  comparison_value, error)
                self.log.warning(message)
                return False, error
        # LESS THAN, LESS THAN OR EQUALS TO, GREATER THAN, GREATER THAN OR EQUALS TO (Semantic version)
        elif 6 <= comparator <= 9:
            try:
                if semver.VersionInfo.parse(str(user_value).strip()).match(
                        self.SEMANTIC_VERSION_COMPARATORS[comparator - 6] + str(comparison_value).strip()
                ):
                    log_builder and log_builder.append(self._format_rule(comparison_attribute, comparator, comparison_value))
                    return True, error
            except ValueError as e:
                error = 'Validation error: ' + str(e)
                message = self._format_error_rule(comparison_attribute, comparator,
                                                  comparison_value, error)
                self.log.warning(message)
                return False, error
        # =, <>, <, <=, >, >= (Number)
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
                    log_builder and log_builder.append(self._format_rule(comparison_attribute, comparator, comparison_value))
                    return True, error
            except Exception as e:
                error = 'Validation error: ' + str(e)
                message = self._format_error_rule(comparison_attribute, comparator, comparison_value, error)
                self.log.warning(message)
                return False, error
        # IS ONE OF (hashed)
        elif comparator == 16:
            if sha256(user_value, salt, context_salt) in [x.strip() for x in comparison_value]:
                return True, error
        # IS NOT ONE OF (hashed)
        elif comparator == 17:
            if sha256(user_value, salt, context_salt) not in [x.strip() for x in comparison_value]:
                return True, error
        # BEFORE, AFTER (UTC DateTime)
        elif 18 <= comparator <= 19:
            try:
                user_value_float = float(str(user_value).replace(",", "."))
                comparison_value_float = float(str(comparison_value).replace(",", "."))

                if (comparator == 18 and user_value_float < comparison_value_float) \
                        or (comparator == 19 and user_value_float > comparison_value_float):
                    return True, error

            except Exception as e:
                error = 'Validation error: ' + str(e)
                message = self._format_error_rule(comparison_attribute, comparator, comparison_value, error)
                self.log.warning(message)
                return False, error
        # EQUALS (hashed)
        elif comparator == 20:
            if sha256(user_value, salt, context_salt) == comparison_value:
                return True, error
        # NOT EQUALS (hashed)
        elif comparator == 21:
            if sha256(user_value, salt, context_salt) != comparison_value:
                return True, error
        # STARTS WITH ANY OF, ENDS WITH ANY OF (hashed)
        elif 22 <= comparator <= 23:
            try:
                for comparison in comparison_value:
                    underscore_index = comparison.index('_')
                    length = int(comparison[:underscore_index])

                    if len(user_value) >= length:
                        comparison_string = comparison[underscore_index + 1:]
                        if (
                            (comparator == 22 and sha256(user_value[:length], salt, context_salt) == comparison_string)
                            or
                            (comparator == 23 and sha256(user_value[-length:], salt, context_salt) == comparison_string)
                        ):
                            return True, error

            except Exception as e:
                error = 'Validation error: ' + str(e)
                message = self._format_error_rule(comparison_attribute, comparator, comparison_value, error)
                self.log.warning(message)
                return False, error
        # ARRAY CONTAINS (hashed)
        elif comparator == 24:
            if comparison_value in [sha256(x.strip(), salt, context_salt) for x in str(user_value).split(',')]:
                return True, error
        # ARRAY NOT CONTAINS (hashed)
        elif comparator == 25:
            if comparison_value not in [sha256(x.strip(), salt, context_salt) for x in str(user_value).split(',')]:
                return True, error

        return False, error
