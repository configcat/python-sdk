import json
from enum import IntEnum

import hashlib
import semver

from .evaluationcontext import EvaluationContext
from .evaluationlogbuilder import EvaluationLogBuilder
from .logger import Logger

from .constants import TARGETING_RULES, VALUE, VARIATION_ID, COMPARISON_ATTRIBUTE, \
    COMPARATOR, PERCENTAGE, SERVED_VALUE, CONDITIONS, PERCENTAGE_OPTIONS, PERCENTAGE_RULE_ATTRIBUTE, \
    COMPARISON_RULE, STRING_LIST_VALUE, DOUBLE_VALUE, STRING_VALUE, FEATURE_FLAGS, \
    SEGMENT_CONDITION, PREREQUISITE_FLAG_CONDITION, SEGMENT_COMPARATOR, SEGMENT_RULES, SEGMENT_NAME, \
    PREREQUISITE_FLAG_KEY, PREREQUISITE_COMPARATOR, BOOL_VALUE, INT_VALUE, TARGETING_RULE_PERCENTAGE_OPTIONS, \
    INLINE_SEGMENT, INLINE_SALT
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


class PrerequisiteComparator(IntEnum):
    EQUALS = 0
    NOT_EQUALS = 1


class SegmentComparator(IntEnum):
    IS_IN = 0
    IS_NOT_IN = 1


class Comparator(IntEnum):
    IS_ONE_OF = 0
    IS_NOT_ONE_OF = 1
    CONTAINS_ANY_OF = 2
    NOT_CONTAINS_ANY_OF = 3
    IS_ONE_OF_SEMVER = 4
    IS_NOT_ONE_OF_SEMVER = 5
    LESS_THAN_SEMVER = 6
    LESS_THAN_OR_EQUAL_SEMVER = 7
    GREATER_THAN_SEMVER = 8
    GREATER_THAN_OR_EQUAL_SEMVER = 9
    EQUALS_NUMBER = 10
    NOT_EQUALS_NUMBER = 11
    LESS_THAN_NUMBER = 12
    LESS_THAN_OR_EQUAL_NUMBER = 13
    GREATER_THAN_NUMBER = 14
    GREATER_THAN_OR_EQUAL_NUMBER = 15
    IS_ONE_OF_HASHED = 16
    IS_NOT_ONE_OF_HASHED = 17
    BEFORE_DATETIME = 18
    AFTER_DATETIME = 19
    EQUALS_HASHED = 20
    NOT_EQUALS_HASHED = 21
    STARTS_WITH_ANY_OF_HASHED = 22
    NOT_STARTS_WITH_ANY_OF_HASHED = 23
    ENDS_WITH_ANY_OF_HASHED = 24
    NOT_ENDS_WITH_ANY_OF_HASHED = 25
    ARRAY_CONTAINS_ANY_OF_HASHED = 26
    ARRAY_NOT_CONTAINS_ANY_OF_HASHED = 27


class RolloutEvaluator(object):
    COMPARATOR_TEXTS = [
        'IS ONE OF',                 # IS_ONE_OF
        'IS NOT ONE OF',             # IS_NOT_ONE_OF
        'CONTAINS ANY OF',           # CONTAINS_ANY_OF
        'NOT CONTAINS ANY OF',       # NOT_CONTAINS_ANY_OF
        'IS ONE OF',                 # IS_ONE_OF_SEMVER
        'IS NOT ONE OF',             # IS_NOT_ONE_OF_SEMVER
        '<',                         # LESS_THAN_SEMVER
        '<=',                        # LESS_THAN_OR_EQUAL_SEMVER
        '>',                         # GREATER_THAN_SEMVER
        '>=',                        # GREATER_THAN_OR_EQUAL_SEMVER
        '=',                         # EQUALS_NUMBER
        '!=',                        # NOT_EQUALS_NUMBER
        '<',                         # LESS_THAN_NUMBER
        '<=',                        # LESS_THAN_OR_EQUAL_NUMBER
        '>',                         # GREATER_THAN_NUMBER
        '>=',                        # GREATER_THAN_OR_EQUAL_NUMBER
        'IS ONE OF',                 # IS_ONE_OF_HASHED
        'IS NOT ONE OF',             # IS_NOT_ONE_OF_HASHED
        'BEFORE',                    # BEFORE_DATETIME
        'AFTER',                     # AFTER_DATETIME
        'EQUALS',                    # EQUALS_HASHED
        'NOT EQUALS',                # NOT_EQUALS_HASHED
        'STARTS WITH ANY OF',        # STARTS_WITH_ANY_OF_HASHED
        'NOT STARTS WITH ANY OF',    # NOT_STARTS_WITH_ANY_OF_HASHED
        'ENDS WITH ANY OF',          # ENDS_WITH_ANY_OF_HASHED
        'NOT ENDS WITH ANY OF',      # NOT_ENDS_WITH_ANY_OF_HASHED
        'ARRAY CONTAINS ANY OF',     # ARRAY_CONTAINS_ANY_OF_HASHED
        'ARRAY NOT CONTAINS ANY OF'  # ARRAY_NOT_CONTAINS_ANY_OF_HASHED
    ]
    COMPARISON_VALUES = [
        STRING_LIST_VALUE,  # IS_ONE_OF
        STRING_LIST_VALUE,  # IS_NOT_ONE_OF
        STRING_LIST_VALUE,  # CONTAINS_ANY_OF
        STRING_LIST_VALUE,  # NOT_CONTAINS_ANY_OF
        STRING_LIST_VALUE,  # IS_ONE_OF_SEMVER
        STRING_LIST_VALUE,  # IS_NOT_ONE_OF_SEMVER
        STRING_VALUE,       # LESS_THAN_SEMVER
        STRING_VALUE,       # LESS_THAN_OR_EQUAL_SEMVER
        STRING_VALUE,       # GREATER_THAN_SEMVER
        STRING_VALUE,       # GREATER_THAN_OR_EQUAL_SEMVER
        DOUBLE_VALUE,       # EQUALS_NUMBER
        DOUBLE_VALUE,       # NOT_EQUALS_NUMBER
        DOUBLE_VALUE,       # LESS_THAN_NUMBER
        DOUBLE_VALUE,       # LESS_THAN_OR_EQUAL_NUMBER
        DOUBLE_VALUE,       # GREATER_THAN_NUMBER
        DOUBLE_VALUE,       # GREATER_THAN_OR_EQUAL_NUMBER
        STRING_LIST_VALUE,  # IS_ONE_OF_HASHED
        STRING_LIST_VALUE,  # IS_NOT_ONE_OF_HASHED
        DOUBLE_VALUE,       # BEFORE_DATETIME
        DOUBLE_VALUE,       # AFTER_DATETIME
        STRING_VALUE,       # EQUALS_HASHED
        STRING_VALUE,       # NOT_EQUALS_HASHED
        STRING_LIST_VALUE,  # STARTS_WITH_ANY_OF_HASHED
        STRING_LIST_VALUE,  # NOT_STARTS_WITH_ANY_OF_HASHED
        STRING_LIST_VALUE,  # ENDS_WITH_ANY_OF_HASHED
        STRING_LIST_VALUE,  # NOT_ENDS_WITH_ANY_OF_HASHED
        STRING_LIST_VALUE,  # ARRAY_CONTAINS_ANY_OF_HASHED
        STRING_LIST_VALUE   # ARRAY_NOT_CONTAINS_ANY_OF_HASHED
    ]
    SEGMENT_COMPARATOR_TEXTS = ['IS IN SEGMENT', 'IS NOT IN SEGMENT']
    PREREQUISITE_COMPARATOR_TEXTS = ['EQUALS', 'DOES NOT EQUAL']

    def __init__(self, log):
        self.log = log

    def evaluate(self, key, user, default_value, default_variation_id, config, log_builder, visited_keys=None):  # noqa: C901
        """
        returns value, variation_id, matched_targeting_rule, matched_percentage_rule, error
        """

        if visited_keys is None:
            visited_keys = []
        is_root_flag_evaluation = len(visited_keys) == 0

        settings = config.get(FEATURE_FLAGS, {})
        setting_descriptor = settings.get(key)

        if setting_descriptor is None:
            error = 'Failed to evaluate setting \'%s\' (the key was not found in config JSON). ' \
                    'Returning the `%s` parameter that you specified in your application: \'%s\'. ' \
                    'Available keys: [%s].'
            error_args = (key, 'default_value', str(default_value), ', '.join("'{}'".format(s) for s in list(settings)))
            self.log.error(error, *error_args, event_id=1001)
            return default_value, default_variation_id, None, None, Logger.format(error, error_args)

        salt = setting_descriptor.get(INLINE_SALT, '')
        targeting_rules = setting_descriptor.get(TARGETING_RULES, [])
        percentage_rule_attribute = setting_descriptor.get(PERCENTAGE_RULE_ATTRIBUTE)

        context = EvaluationContext(key, user, visited_keys)

        user_has_invalid_type = context.user is not None and not isinstance(context.user, User)
        if user_has_invalid_type:
            self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                             '(User Object is not an instance of User type). '
                             'You should pass a User Object to the evaluation methods like `get_value()` '
                             'in order to make targeting work properly. '
                             'Read more: https://configcat.com/docs/advanced/user-object/',
                             key, event_id=4001)
            # We set the user to None and won't log further missing user object warnings
            context.user = None
            context.is_missing_user_object_logged = True

        try:
            if log_builder and is_root_flag_evaluation:
                log_builder.append("Evaluating '{}'".format(key))
                log_builder.append(" for User '{}'".format(context.user) if context.user is not None else '')
                log_builder.increase_indent()

            # Evaluate targeting rules (logically connected by OR)
            if log_builder and len(targeting_rules) > 0:
                log_builder.new_line('Evaluating targeting rules and applying the first match if any:')
            for targeting_rule in targeting_rules:
                conditions = targeting_rule.get(CONDITIONS, [])

                if len(conditions) > 0:
                    served_value = targeting_rule.get(SERVED_VALUE)
                    value = get_value(served_value) if served_value is not None else None

                    # Evaluate targeting rule conditions (logically connected by AND)
                    if self._evaluate_conditions(conditions, context, salt, config, log_builder, value):
                        if served_value is not None:
                            variation_id = served_value.get(VARIATION_ID, default_variation_id)
                            log_builder and is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % value)
                            return value, variation_id, targeting_rule, None, None
                    else:
                        continue

                # Evaluate percentage options of the targeting rule
                log_builder and log_builder.increase_indent()
                percentage_options = targeting_rule.get(TARGETING_RULE_PERCENTAGE_OPTIONS, [])
                percentage_evaluation_result, percentage_value, percentage_variation_id, percentage_option = \
                    self._evaluate_percentage_options(percentage_options, context, percentage_rule_attribute,
                                                      default_variation_id, log_builder)

                if percentage_evaluation_result:
                    if log_builder:
                        log_builder.decrease_indent()
                        is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % percentage_value)
                    return percentage_value, percentage_variation_id, targeting_rule, percentage_option, None
                else:
                    if log_builder:
                        log_builder.new_line(
                            'The current targeting rule is ignored and the evaluation continues with the next rule.')
                        log_builder.decrease_indent()
                    continue

            # Evaluate percentage options
            percentage_options = setting_descriptor.get(PERCENTAGE_OPTIONS, [])
            percentage_evaluation_result, percentage_value, percentage_variation_id, percentage_option = \
                self._evaluate_percentage_options(percentage_options, context, percentage_rule_attribute,
                                                  default_variation_id, log_builder)
            if percentage_evaluation_result:
                log_builder and is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % percentage_value)
                return percentage_value, percentage_variation_id, None, percentage_option, None

            return_value = get_value(setting_descriptor)
            return_variation_id = setting_descriptor.get(VARIATION_ID, default_variation_id)
            log_builder and is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % return_value)
            return return_value, return_variation_id, None, None, None
        except Exception as e:
            error = 'Failed to evaluate setting \'%s\'. (%s). ' \
                    'Returning the `%s` parameter that you specified in your application: \'%s\'. '
            error_args = (key, str(e), 'default_value', str(default_value))
            self.log.error(error, *error_args, event_id=2001)
            return default_value, default_variation_id, None, None, Logger.format(error, error_args)

    def _format_rule(self, comparison_attribute, comparator, comparison_value):
        comparator_text = self.COMPARATOR_TEXTS[comparator]
        return "User.%s %s %s" \
               % (comparison_attribute, comparator_text,
                  EvaluationLogBuilder.trunc_comparison_value_if_needed(comparator, comparison_value))

    def _handle_invalid_user_attribute(self, comparison_attribute, comparator, comparison_value, key, validation_error):
        """
        returns: evaluation error message
        """
        error = 'cannot evaluate, the User.%s attribute is invalid (%s)' % (comparison_attribute, validation_error)
        self.log.warning('Cannot evaluate condition (%s) for setting \'%s\' '
                         '(%s). Please check the User.%s attribute and make sure that its value corresponds to the '
                         'comparison operator.',
                         self._format_rule(comparison_attribute, comparator, comparison_value), key,
                         validation_error, comparison_attribute, event_id=3004)
        return error

    def _evaluate_percentage_options(self, percentage_options, context, percentage_rule_attribute, default_variation_id, log_builder):  # noqa: C901, E501
        """
        returns: evaluation_result, percentage_value, percentage_variation_id, percentage_option
        """
        if len(percentage_options) == 0:
            return False, None, None, None

        user = context.user
        key = context.key

        if user is None:
            if not context.is_missing_user_object_logged:
                self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                                 '(User Object is missing). '
                                 'You should pass a User Object to the evaluation methods like `get_value()` '
                                 'in order to make targeting work properly. '
                                 'Read more: https://configcat.com/docs/advanced/user-object/',
                                 key, event_id=3001)
                context.is_missing_user_object_logged = True

            if log_builder:
                log_builder.new_line('Skipping % options because the User Object is missing.')
            return False, None, None, None

        user_attribute_name = percentage_rule_attribute if percentage_rule_attribute is not None else 'Identifier'
        user_key = user.get_attribute(percentage_rule_attribute) if percentage_rule_attribute is not None \
            else user.get_identifier()
        if percentage_rule_attribute is not None and user_key is None:
            if not context.is_missing_user_object_attribute_logged:
                self.log.warning('Cannot evaluate %% options for setting \'%s\' '
                                 '(the User.%s attribute is missing). You should set the User.%s attribute in order to make '
                                 'targeting work properly. Read more: https://configcat.com/docs/advanced/user-object/',
                                 key, percentage_rule_attribute, percentage_rule_attribute,
                                 event_id=3003)
                context.is_missing_user_object_attribute_logged = True

            if log_builder:
                log_builder.new_line(
                    'Skipping %% options because the User.%s attribute is missing.' % user_attribute_name)
            return False, None, None, None

        hash_candidate = ('%s%s' % (key, user_key)).encode('utf-8')
        hash_val = int(hashlib.sha1(hash_candidate).hexdigest()[:7], 16) % 100

        bucket = 0
        index = 1
        for percentage_option in percentage_options or []:
            percentage = percentage_option.get(PERCENTAGE, 0)
            bucket += percentage
            if hash_val < bucket:
                percentage_value = get_value(percentage_option)
                variation_id = percentage_option.get(VARIATION_ID, default_variation_id)
                if log_builder:
                    log_builder.new_line('Evaluating %% options based on the User.%s attribute:' %
                                         user_attribute_name)
                    log_builder.new_line('- Computing hash in the [0..99] range from User.%s => %s '
                                         '(this value is sticky and consistent across all SDKs)' %
                                         (user_attribute_name, hash_val))
                    log_builder.new_line("- Hash value %s selects %% option %s (%s%%), '%s'." %
                                         (hash_val, index, percentage, percentage_value))
                return True, percentage_value, variation_id, percentage_option
            index += 1

        return False, None, None, None

    def _evaluate_conditions(self, conditions, context, salt, config, log_builder, value):  # noqa: C901
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
                result, error = self._evaluate_comparison_rule_condition(comparison_rule, context, context.key, salt,
                                                                         log_builder)
                if log_builder and len(conditions) > 1:
                    log_builder.append('=> {}'.format('true' if result else 'false'))
                    if not result:
                        log_builder.append(', skipping the remaining AND conditions')

                if not result:
                    condition_result = False
                    break
            elif segment_condition is not None:
                result, error = self._evaluate_segment_condition(segment_condition, context, salt, log_builder)
                if log_builder:
                    if len(conditions) > 1:
                        log_builder.append(' => {}'.format('true' if result else 'false'))
                        if not result:
                            log_builder.append(', skipping the remaining AND conditions')
                    elif error is None:
                        log_builder.new_line()

                if not result:
                    condition_result = False
                    break
            elif prerequisite_flag_condition is not None:
                result, error = self._evaluate_prerequisite_flag_condition(prerequisite_flag_condition, context, config,
                                                                           log_builder)
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

    def _evaluate_prerequisite_flag_condition(self, prerequisite_flag_condition, context, config, log_builder):  # noqa: C901, E501
        prerequisite_key = prerequisite_flag_condition.get(PREREQUISITE_FLAG_KEY)
        prerequisite_comparator = prerequisite_flag_condition.get(PREREQUISITE_COMPARATOR)

        # Check if the prerequisite key exists
        settings = config.get(FEATURE_FLAGS, {})
        if prerequisite_key is None or settings.get(prerequisite_key) is None:
            raise KeyError('Prerequisite flag key is missing or invalid.')

        prerequisite_condition_result = False
        try:
            prerequisite_comparison_value = get_value(prerequisite_flag_condition)
        except ValueError as e:
            log_builder and log_builder.new_line('Prerequisite comparison value error: %s' % str(e))
            return prerequisite_condition_result, None

        prerequisite_condition = ("Flag '%s' %s '%s'" %
                                  (prerequisite_key, self.PREREQUISITE_COMPARATOR_TEXTS[prerequisite_comparator],
                                   str(prerequisite_comparison_value)))

        # Circular dependency check
        visited_keys = context.visited_keys
        visited_keys.append(context.key)
        if prerequisite_key in visited_keys:
            depending_flags = ' -> '.join("'{}'".format(s) for s in list(visited_keys) + [prerequisite_key])
            error = 'Cannot evaluate condition (%s) for setting \'%s\' (circular dependency detected between the following ' \
                    'depending flags: %s). Please check your feature flag definition and eliminate the circular dependency.'
            error_args = (prerequisite_condition, context.key, depending_flags)
            self.log.warning(error, *error_args, event_id=3005)
            if log_builder:
                log_builder.append(prerequisite_condition + ' ')

            if visited_keys:
                visited_keys.pop()

            return prerequisite_condition_result, 'cannot evaluate, circular dependency detected'

        if log_builder:
            log_builder.append(prerequisite_condition)
            log_builder.new_line('(').increase_indent()
            log_builder.new_line("Evaluating prerequisite flag '%s':" % prerequisite_key)

        prerequisite_value, _, _, _, error = self.evaluate(prerequisite_key, context.user, None, None, config,
                                                           log_builder, context.visited_keys)

        if visited_keys:
            visited_keys.pop()

        if error is not None:
            return prerequisite_condition_result, error

        if log_builder:
            log_builder.new_line("Prerequisite flag evaluation result: '%s'." % str(prerequisite_value))
            log_builder.new_line("Condition (Flag '%s' %s '%s') evaluates to " %
                                 (prerequisite_key, self.PREREQUISITE_COMPARATOR_TEXTS[prerequisite_comparator],
                                  str(prerequisite_comparison_value)))

        # EQUALS
        if prerequisite_comparator == PrerequisiteComparator.EQUALS:
            if prerequisite_value == prerequisite_comparison_value:
                prerequisite_condition_result = True
        # DOES NOT EQUAL
        elif prerequisite_comparator == PrerequisiteComparator.NOT_EQUALS:
            if prerequisite_value != prerequisite_comparison_value:
                prerequisite_condition_result = True

        if log_builder:
            log_builder.append('%s.' % ('true' if prerequisite_condition_result else 'false'))
            log_builder.decrease_indent().new_line(')').new_line()

        return prerequisite_condition_result, None

    def _evaluate_segment_condition(self, segment_condition, context, salt, log_builder):  # noqa: C901
        user = context.user
        key = context.key

        segment = segment_condition[INLINE_SEGMENT]
        segment_name = segment.get(SEGMENT_NAME, '')
        segment_comparator = segment_condition.get(SEGMENT_COMPARATOR)
        segment_comparison_rules = segment.get(SEGMENT_RULES, [])

        if user is None:
            if not context.is_missing_user_object_logged:
                self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                                 '(User Object is missing). '
                                 'You should pass a User Object to the evaluation methods like `get_value()` '
                                 'in order to make targeting work properly. '
                                 'Read more: https://configcat.com/docs/advanced/user-object/',
                                 key, event_id=3001)
                context.is_missing_user_object_logged = True
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

                result, error = self._evaluate_comparison_rule_condition(segment_comparison_rule, context,
                                                                         segment_name, salt, log_builder)
                if log_builder:
                    log_builder.append('=> {}'.format('true' if result else 'false'))
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
                                      segment_name, 'true' if segment_condition_result else 'false'))
                log_builder.decrease_indent().new_line(')')
            return segment_condition_result, error

        return False, None

    def _evaluate_comparison_rule_condition(self, comparison_rule, context, context_salt, salt, log_builder):  # noqa: C901, E501
        """
        returns result of comparison rule condition, error
        """

        user = context.user
        key = context.key

        comparison_attribute = comparison_rule.get(COMPARISON_ATTRIBUTE)
        comparator = comparison_rule.get(COMPARATOR)
        comparison_value = comparison_rule.get(self.COMPARISON_VALUES[comparator])
        error = None

        if log_builder:
            log_builder.append(self._format_rule(comparison_attribute, comparator, comparison_value) + ' ')

        if user is None:
            if not context.is_missing_user_object_logged:
                self.log.warning('Cannot evaluate targeting rules and %% options for setting \'%s\' '
                                 '(User Object is missing). '
                                 'You should pass a User Object to the evaluation methods like `get_value()` '
                                 'in order to make targeting work properly. '
                                 'Read more: https://configcat.com/docs/advanced/user-object/',
                                 key, event_id=3001)
                context.is_missing_user_object_logged = True
            error = 'cannot evaluate, User Object is missing'
            return False, error

        user_value = user.get_attribute(comparison_attribute)
        if user_value is None or not user_value:
            self.log.warning('Cannot evaluate condition (%s) for setting \'%s\' '
                             '(the User.%s attribute is missing). You should set the User.%s attribute in order to make '
                             'targeting work properly. Read more: https://configcat.com/docs/advanced/user-object/',
                             self._format_rule(comparison_attribute, comparator, comparison_value), key,
                             comparison_attribute, comparison_attribute,
                             event_id=3003)
            error = 'cannot evaluate, the User.{} attribute is missing'.format(comparison_attribute)
            return False, error

        # IS ONE OF
        if comparator == Comparator.IS_ONE_OF:
            if str(user_value) in [x.strip() for x in comparison_value]:
                return True, error
        # IS NOT ONE OF
        elif comparator == Comparator.IS_NOT_ONE_OF:
            if str(user_value) not in [x.strip() for x in comparison_value]:
                return True, error
        # CONTAINS ANY OF
        elif comparator == Comparator.CONTAINS_ANY_OF:
            for comparison in comparison_value:
                if str(comparison) in str(user_value):
                    return True, error
        # NOT CONTAINS ANY OF
        elif comparator == Comparator.NOT_CONTAINS_ANY_OF:
            if not any(str(comparison) in str(user_value) for comparison in comparison_value):
                return True, error
        # IS ONE OF, IS NOT ONE OF (Semantic version)
        elif Comparator.IS_ONE_OF_SEMVER <= comparator <= Comparator.IS_NOT_ONE_OF_SEMVER:
            try:
                match = False
                for x in filter(None, [x.strip() for x in comparison_value]):
                    match = semver.VersionInfo.parse(str(user_value).strip()).match('==' + x) or match
                if (match and comparator == Comparator.IS_ONE_OF_SEMVER) \
                        or (not match and comparator == Comparator.IS_NOT_ONE_OF_SEMVER):
                    return True, error
            except ValueError:
                validation_error = "'%s' is not a valid semantic version" % str(user_value).strip()
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error
        # LESS THAN, LESS THAN OR EQUALS TO, GREATER THAN, GREATER THAN OR EQUALS TO (Semantic version)
        elif Comparator.LESS_THAN_SEMVER <= comparator <= Comparator.GREATER_THAN_OR_EQUAL_SEMVER:
            try:
                if semver.VersionInfo.parse(str(user_value).strip()).match(
                        self.COMPARATOR_TEXTS[comparator] + str(comparison_value).strip()
                ):
                    return True, error
            except ValueError:
                validation_error = "'%s' is not a valid semantic version" % str(user_value).strip()
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error
        # =, <>, <, <=, >, >= (number)
        elif Comparator.EQUALS_NUMBER <= comparator <= Comparator.GREATER_THAN_OR_EQUAL_NUMBER:
            try:
                user_value_float = float(str(user_value).replace(",", "."))
            except ValueError:
                validation_error = "'%s' is not a valid decimal number" % str(user_value)
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error

            comparison_value_float = float(str(comparison_value).replace(",", "."))

            if (comparator == Comparator.EQUALS_NUMBER and user_value_float == comparison_value_float) \
                    or (comparator == Comparator.NOT_EQUALS_NUMBER and user_value_float != comparison_value_float) \
                    or (comparator == Comparator.LESS_THAN_NUMBER and user_value_float < comparison_value_float) \
                    or (comparator == Comparator.LESS_THAN_OR_EQUAL_NUMBER and user_value_float <= comparison_value_float) \
                    or (comparator == Comparator.GREATER_THAN_NUMBER and user_value_float > comparison_value_float) \
                    or (comparator == Comparator.GREATER_THAN_OR_EQUAL_NUMBER and user_value_float >= comparison_value_float):
                return True, error
        # IS ONE OF (hashed)
        elif comparator == Comparator.IS_ONE_OF_HASHED:
            if sha256(user_value, salt, context_salt) in comparison_value:
                return True, error
        # IS NOT ONE OF (hashed)
        elif comparator == Comparator.IS_NOT_ONE_OF_HASHED:
            if sha256(user_value, salt, context_salt) not in comparison_value:
                return True, error
        # BEFORE, AFTER (UTC datetime)
        elif Comparator.BEFORE_DATETIME <= comparator <= Comparator.AFTER_DATETIME:
            try:
                user_value_float = float(str(user_value).replace(",", "."))
            except ValueError:
                validation_error = "'%s' is not a valid Unix timestamp (number of seconds elapsed since Unix epoch)" % \
                                   str(user_value)
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error

            comparison_value_float = float(str(comparison_value).replace(",", "."))

            if (comparator == Comparator.BEFORE_DATETIME and user_value_float < comparison_value_float) \
                    or (comparator == Comparator.AFTER_DATETIME and user_value_float > comparison_value_float):
                return True, error

        # EQUALS (hashed)
        elif comparator == Comparator.EQUALS_HASHED:
            if sha256(user_value, salt, context_salt) == comparison_value:
                return True, error
        # NOT EQUALS (hashed)
        elif comparator == Comparator.NOT_EQUALS_HASHED:
            if sha256(user_value, salt, context_salt) != comparison_value:
                return True, error
        # STARTS WITH ANY OF, NOT STARTS WITH ANY OF, ENDS WITH ANY OF, NOT ENDS WITH ANY OF (hashed)
        elif Comparator.STARTS_WITH_ANY_OF_HASHED <= comparator <= Comparator.NOT_ENDS_WITH_ANY_OF_HASHED:
            for comparison in comparison_value:
                underscore_index = comparison.index('_')
                length = int(comparison[:underscore_index])

                if len(user_value) >= length:
                    comparison_string = comparison[underscore_index + 1:]
                    if (
                            (comparator == Comparator.STARTS_WITH_ANY_OF_HASHED
                             and sha256(user_value[:length], salt, context_salt) == comparison_string)
                            or
                            (comparator == Comparator.NOT_STARTS_WITH_ANY_OF_HASHED
                             and sha256(user_value[:length], salt, context_salt) != comparison_string)
                            or
                            (comparator == Comparator.ENDS_WITH_ANY_OF_HASHED
                             and sha256(user_value[-length:], salt, context_salt) == comparison_string)
                            or
                            (comparator == Comparator.NOT_ENDS_WITH_ANY_OF_HASHED
                             and sha256(user_value[-length:], salt, context_salt) != comparison_string)
                    ):
                        return True, error
        # ARRAY CONTAINS ANY OF, ARRAY NOT CONTAINS ANY OF (hashed)
        elif Comparator.ARRAY_CONTAINS_ANY_OF_HASHED <= comparator <= Comparator.ARRAY_NOT_CONTAINS_ANY_OF_HASHED:
            try:
                user_value_list = json.loads(user_value)
                if not isinstance(user_value_list, list):
                    raise ValueError()
            except ValueError:
                validation_error = "'%s' is not a valid JSON string array" % str(user_value)
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error

            for comparison in comparison_value:
                if comparator == Comparator.ARRAY_CONTAINS_ANY_OF_HASHED:
                    if comparison in [sha256(x.strip(), salt, context_salt) for x in user_value_list]:
                        return True, error
                else:
                    if comparison not in [sha256(x.strip(), salt, context_salt) for x in user_value_list]:
                        return True, error

        return False, error
