import json

import hashlib
import sys
import semver

from .config import FEATURE_FLAGS, INLINE_SALT, TARGETING_RULES, PERCENTAGE_RULE_ATTRIBUTE, CONDITIONS, SERVED_VALUE, \
    get_value, VARIATION_ID, TARGETING_RULE_PERCENTAGE_OPTIONS, PERCENTAGE_OPTIONS, PERCENTAGE, USER_CONDITION, \
    SEGMENT_CONDITION, PREREQUISITE_FLAG_CONDITION, PREREQUISITE_FLAG_KEY, PREREQUISITE_COMPARATOR, \
    PrerequisiteComparator, INLINE_SEGMENT, SEGMENT_NAME, SEGMENT_COMPARATOR, SEGMENT_CONDITIONS, SegmentComparator, \
    COMPARISON_ATTRIBUTE, COMPARATOR, Comparator, COMPARATOR_TEXTS, PREREQUISITE_COMPARATOR_TEXTS, \
    SEGMENT_COMPARATOR_TEXTS, COMPARISON_VALUES, get_value_type, SETTING_TYPE, SettingType
from .evaluationcontext import EvaluationContext
from .evaluationlogbuilder import EvaluationLogBuilder
from .logger import Logger
from datetime import datetime

from .user import User
from .utils import unicode_to_utf8, encode_utf8, get_seconds_since_epoch


def sha256(value_utf8, salt, context_salt):
    """
    Calculates the SHA256 hash of the given value with the given salt and context_salt.
    """
    return hashlib.sha256(value_utf8 + salt.encode('utf-8') + context_salt.encode('utf-8')).hexdigest()


class RolloutEvaluator(object):
    def __init__(self, log):
        self.log = log

    def evaluate(self, key, user, default_value, default_variation_id, config, log_builder, visited_keys=None):  # noqa: C901
        """
        returns value, variation_id, matched_targeting_rule, matched_percentage_option, error
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

        setting_type = setting_descriptor.get(SETTING_TYPE)
        salt = setting_descriptor.get(INLINE_SALT, '')
        targeting_rules = setting_descriptor.get(TARGETING_RULES, [])
        percentage_rule_attribute = setting_descriptor.get(PERCENTAGE_RULE_ATTRIBUTE)

        context = EvaluationContext(key, setting_type, user, visited_keys)

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
                    value = get_value(served_value, setting_type) if served_value is not None else None

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

            return_value = get_value(setting_descriptor, setting_type)
            return_variation_id = setting_descriptor.get(VARIATION_ID, default_variation_id)
            log_builder and is_root_flag_evaluation and log_builder.new_line("Returning '%s'." % return_value)
            return return_value, return_variation_id, None, None, None
        except Exception as e:
            # During the recursive evaluation of a prerequisite flag, we propagate the exceptions
            # and let the root flag's evaluation code handle them.
            if not is_root_flag_evaluation:
                raise e

            error = 'Failed to evaluate setting \'%s\'. (%s). ' \
                    'Returning the `%s` parameter that you specified in your application: \'%s\'. '
            error_args = (key, str(e), 'default_value', str(default_value))
            self.log.error(error, *error_args, event_id=2001)
            return default_value, default_variation_id, None, None, Logger.format(error, error_args)

    def _format_rule(self, comparison_attribute, comparator, comparison_value):
        comparator_text = COMPARATOR_TEXTS[comparator]
        return "User.%s %s %s" \
               % (comparison_attribute, comparator_text,
                  EvaluationLogBuilder.trunc_comparison_value_if_needed(comparator, comparison_value))

    def _user_attribute_value_to_string(self, value):
        if value is None:
            return None

        if isinstance(value, datetime):
            value = self._get_user_attribute_value_as_seconds_since_epoch(value)
        elif isinstance(value, list):
            value = self._get_user_attribute_value_as_string_list(value)

        return str(value)

    def _get_user_attribute_value_as_text(self, attribute_name, attribute_value, condition, key):
        if isinstance(attribute_value, str):
            return attribute_value

        if sys.version_info[0] == 2 and isinstance(attribute_value, unicode):  # noqa: F821
            return attribute_value  # Handle unicode strings on Python 2.7

        self.log.warning('Evaluation of condition (%s) for setting \'%s\' may not produce the expected result '
                         '(the User.%s attribute is not a string value, thus it was automatically converted to '
                         'the string value \'%s\'). Please make sure that using a non-string value was intended.',
                         condition, key, attribute_name, attribute_value, event_id=3005)
        return self._user_attribute_value_to_string(attribute_value)

    def _convert_numeric_to_float(self, value):
        if isinstance(value, str):
            return float(value.replace(",", "."))

        if sys.version_info[0] == 2 and isinstance(value, unicode):  # noqa: F821
            return float(value.replace(",", "."))  # Handle unicode strings on Python 2.7

        return float(value)

    def _get_user_attribute_value_as_seconds_since_epoch(self, attribute_value):
        if isinstance(attribute_value, datetime):
            return get_seconds_since_epoch(attribute_value)

        return self._convert_numeric_to_float(attribute_value)

    def _get_user_attribute_value_as_string_list(self, attribute_value):
        if not isinstance(attribute_value, list):
            attribute_value_list = json.loads(attribute_value)
        else:
            attribute_value_list = attribute_value
        if not isinstance(attribute_value_list, list):
            raise ValueError()

        return attribute_value_list

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
        if percentage_rule_attribute is not None:
            user_key = user.get_attribute(percentage_rule_attribute)
        else:
            user_key = user.get_identifier()
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

        hash_candidate = ('%s%s' % (key, self._user_attribute_value_to_string(user_key))).encode('utf-8')
        hash_val = int(hashlib.sha1(hash_candidate).hexdigest()[:7], 16) % 100

        bucket = 0
        index = 1
        for percentage_option in percentage_options or []:
            percentage = percentage_option.get(PERCENTAGE, 0)
            bucket += percentage
            if hash_val < bucket:
                percentage_value = get_value(percentage_option, context.setting_type)
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
            user_condition = condition.get(USER_CONDITION)
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

            if user_condition is not None:
                result, error = self._evaluate_user_condition(user_condition, context, context.key, salt,
                                                              log_builder)
                if log_builder and len(conditions) > 1:
                    log_builder.append('=> {}'.format('true' if result else 'false'))
                    if not result:
                        log_builder.append(', skipping the remaining AND conditions')

                if not result or error:
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

                if not result or error:
                    condition_result = False
                    break
            elif prerequisite_flag_condition is not None:
                result = self._evaluate_prerequisite_flag_condition(prerequisite_flag_condition, context, config, log_builder)
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
            raise ValueError('Prerequisite flag key is missing or invalid.')

        prerequisite_condition_result = False
        prerequisite_flag_setting_type = settings[prerequisite_key].get(SETTING_TYPE)
        prerequisite_comparison_value_type = get_value_type(prerequisite_flag_condition)

        # Type mismatch check
        if prerequisite_comparison_value_type != SettingType.to_type(prerequisite_flag_setting_type):
            raise ValueError("Type mismatch between comparison value type %s and type %s of prerequisite flag '%s'" %
                             (prerequisite_comparison_value_type, SettingType.to_type(prerequisite_flag_setting_type),
                              prerequisite_key))

        prerequisite_comparison_value = get_value(prerequisite_flag_condition, prerequisite_flag_setting_type)

        prerequisite_condition = ("Flag '%s' %s '%s'" %
                                  (prerequisite_key, PREREQUISITE_COMPARATOR_TEXTS[prerequisite_comparator],
                                   str(prerequisite_comparison_value)))

        # Circular dependency check
        visited_keys = context.visited_keys
        visited_keys.append(context.key)
        if prerequisite_key in visited_keys:
            depending_flags = ' -> '.join("'{}'".format(s) for s in list(visited_keys) + [prerequisite_key])
            raise ValueError('Circular dependency detected between the following depending flags: %s.' % depending_flags)

        if log_builder:
            log_builder.append(prerequisite_condition)
            log_builder.new_line('(').increase_indent()
            log_builder.new_line("Evaluating prerequisite flag '%s':" % prerequisite_key)

        prerequisite_value, _, _, _, _ = self.evaluate(prerequisite_key, context.user, None, None, config,
                                                       log_builder, context.visited_keys)

        if visited_keys:
            visited_keys.pop()

        if log_builder:
            log_builder.new_line("Prerequisite flag evaluation result: '%s'." % str(prerequisite_value))
            log_builder.new_line("Condition (Flag '%s' %s '%s') evaluates to " %
                                 (prerequisite_key, PREREQUISITE_COMPARATOR_TEXTS[prerequisite_comparator],
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

        return prerequisite_condition_result

    def _evaluate_segment_condition(self, segment_condition, context, salt, log_builder):  # noqa: C901
        user = context.user
        key = context.key

        segment = segment_condition[INLINE_SEGMENT]
        if segment is None:
            raise ValueError('Segment reference is invalid.')

        segment_name = segment.get(SEGMENT_NAME, '')
        segment_comparator = segment_condition.get(SEGMENT_COMPARATOR)
        segment_conditions = segment.get(SEGMENT_CONDITIONS, [])

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
                log_builder.append("User %s '%s' " % (SEGMENT_COMPARATOR_TEXTS[segment_comparator], segment_name))
            return False, 'cannot evaluate, User Object is missing'

        # IS IN SEGMENT, IS NOT IN SEGMENT
        if segment_comparator in [SegmentComparator.IS_IN, SegmentComparator.IS_NOT_IN]:
            if log_builder:
                log_builder.append("User %s '%s'" %
                                   (SEGMENT_COMPARATOR_TEXTS[segment_comparator], segment_name))
                log_builder.new_line('(').increase_indent()
                log_builder.new_line("Evaluating segment '%s':" % segment_name)

            # Set initial condition result based on comparator
            segment_condition_result = segment_comparator == SegmentComparator.IS_IN

            # Evaluate segment conditions (logically connected by AND)
            first_segment_rule = True
            error = None
            for segment_condition in segment_conditions:
                if first_segment_rule:
                    if log_builder:
                        log_builder.new_line('- IF ')
                        log_builder.increase_indent()
                    first_segment_rule = False
                else:
                    if log_builder:
                        log_builder.new_line('AND ')

                result, error = self._evaluate_user_condition(segment_condition, context, segment_name, salt, log_builder)
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
                log_builder.new_line('Segment evaluation result: ')
                if not error:
                    log_builder.append('User IS%sIN SEGMENT.' % (' ' if segment_evaluation_result else ' NOT '))
                else:
                    log_builder.append('%s.' % error)

                log_builder.new_line("Condition (User %s '%s') " % (SEGMENT_COMPARATOR_TEXTS[segment_comparator],
                                                                    segment_name))
                if not error:
                    log_builder.append("evaluates to %s." % ('true' if segment_condition_result else 'false'))
                else:
                    log_builder.append('failed to evaluate.')

                log_builder.decrease_indent().new_line(')')
                if error:
                    log_builder.new_line()

            return segment_condition_result, error

        return False, None

    def _evaluate_user_condition(self, user_condition, context, context_salt, salt, log_builder):  # noqa: C901, E501
        """
        returns result of user condition, error
        """

        user = context.user
        key = context.key

        comparison_attribute = user_condition.get(COMPARISON_ATTRIBUTE)
        comparator = user_condition.get(COMPARATOR)
        comparison_value = user_condition.get(COMPARISON_VALUES[comparator])
        condition = self._format_rule(comparison_attribute, comparator, comparison_value)
        error = None

        if comparison_attribute is None:
            raise ValueError('Comparison attribute name is missing.')

        if log_builder:
            log_builder.append(condition + ' ')

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
                             condition, key, comparison_attribute, comparison_attribute, event_id=3003)
            error = 'cannot evaluate, the User.{} attribute is missing'.format(comparison_attribute)
            return False, error

        # IS ONE OF
        if comparator == Comparator.IS_ONE_OF:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if user_value in comparison_value:
                return True, error
        # IS NOT ONE OF
        elif comparator == Comparator.IS_NOT_ONE_OF:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if user_value not in comparison_value:
                return True, error
        # CONTAINS ANY OF
        elif comparator == Comparator.CONTAINS_ANY_OF:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            for comparison in comparison_value:
                if comparison in user_value:
                    return True, error
        # NOT CONTAINS ANY OF
        elif comparator == Comparator.NOT_CONTAINS_ANY_OF:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if not any(comparison in user_value for comparison in comparison_value):
                return True, error
        # IS ONE OF, IS NOT ONE OF (Semantic version)
        elif Comparator.IS_ONE_OF_SEMVER <= comparator <= Comparator.IS_NOT_ONE_OF_SEMVER:
            try:
                match = False
                for x in filter(None, [x.strip() for x in comparison_value]):
                    match = semver.VersionInfo.parse(str(user_value).strip()).match('==' + str(x)) or match
                if match == (comparator == Comparator.IS_ONE_OF_SEMVER):
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
                        COMPARATOR_TEXTS[comparator] + str(comparison_value).strip()
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
                user_value_float = self._convert_numeric_to_float(user_value)
            except ValueError:
                validation_error = "'%s' is not a valid decimal number" % str(user_value)
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error

            comparison_value_float = float(comparison_value)

            if (comparator == Comparator.EQUALS_NUMBER and user_value_float == comparison_value_float) \
                    or (comparator == Comparator.NOT_EQUALS_NUMBER and user_value_float != comparison_value_float) \
                    or (comparator == Comparator.LESS_THAN_NUMBER and user_value_float < comparison_value_float) \
                    or (comparator == Comparator.LESS_THAN_OR_EQUAL_NUMBER and user_value_float <= comparison_value_float) \
                    or (comparator == Comparator.GREATER_THAN_NUMBER and user_value_float > comparison_value_float) \
                    or (comparator == Comparator.GREATER_THAN_OR_EQUAL_NUMBER and user_value_float >= comparison_value_float):
                return True, error
        # IS ONE OF (hashed)
        elif comparator == Comparator.IS_ONE_OF_HASHED:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if sha256(encode_utf8(user_value), salt, context_salt) in comparison_value:
                return True, error
        # IS NOT ONE OF (hashed)
        elif comparator == Comparator.IS_NOT_ONE_OF_HASHED:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if sha256(encode_utf8(user_value), salt, context_salt) not in comparison_value:
                return True, error
        # BEFORE, AFTER (UTC datetime)
        elif Comparator.BEFORE_DATETIME <= comparator <= Comparator.AFTER_DATETIME:
            try:
                user_value_float = self._get_user_attribute_value_as_seconds_since_epoch(user_value)
            except ValueError:
                validation_error = "'%s' is not a valid Unix timestamp (number of seconds elapsed since Unix epoch)" % \
                                   str(user_value)
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error

            comparison_value_float = float(comparison_value)

            if (comparator == Comparator.BEFORE_DATETIME and user_value_float < comparison_value_float) \
                    or (comparator == Comparator.AFTER_DATETIME and user_value_float > comparison_value_float):
                return True, error
        # EQUALS (hashed)
        elif comparator == Comparator.EQUALS_HASHED:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if sha256(encode_utf8(user_value), salt, context_salt) == comparison_value:
                return True, error
        # NOT EQUALS (hashed)
        elif comparator == Comparator.NOT_EQUALS_HASHED:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if sha256(encode_utf8(user_value), salt, context_salt) != comparison_value:
                return True, error
        # STARTS WITH ANY OF, NOT STARTS WITH ANY OF, ENDS WITH ANY OF, NOT ENDS WITH ANY OF (hashed)
        elif Comparator.STARTS_WITH_ANY_OF_HASHED <= comparator <= Comparator.NOT_ENDS_WITH_ANY_OF_HASHED:
            for comparison in comparison_value:
                underscore_index = comparison.index('_')
                length = int(comparison[:underscore_index])
                user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
                user_value_utf8 = encode_utf8(user_value)

                if len(user_value_utf8) >= length:
                    comparison_string = comparison[underscore_index + 1:]
                    if (comparator == Comparator.STARTS_WITH_ANY_OF_HASHED
                        and sha256(user_value_utf8[:length], salt, context_salt) == comparison_string) or \
                            (comparator == Comparator.ENDS_WITH_ANY_OF_HASHED
                             and sha256(user_value_utf8[-length:], salt, context_salt) == comparison_string):
                        return True, error
                    elif (comparator == Comparator.NOT_STARTS_WITH_ANY_OF_HASHED
                          and sha256(user_value_utf8[:length], salt, context_salt) == comparison_string) or \
                            (comparator == Comparator.NOT_ENDS_WITH_ANY_OF_HASHED
                             and sha256(user_value_utf8[-length:], salt, context_salt) == comparison_string):
                        return False, None

            # If no matches were found for the NOT_* conditions, then return True
            if comparator in [Comparator.NOT_STARTS_WITH_ANY_OF_HASHED, Comparator.NOT_ENDS_WITH_ANY_OF_HASHED]:
                return True, error
        # ARRAY CONTAINS ANY OF, ARRAY NOT CONTAINS ANY OF (hashed)
        elif Comparator.ARRAY_CONTAINS_ANY_OF_HASHED <= comparator <= Comparator.ARRAY_NOT_CONTAINS_ANY_OF_HASHED:
            try:
                user_value_list = self._get_user_attribute_value_as_string_list(user_value)

                if sys.version_info[0] == 2:
                    user_value_list = unicode_to_utf8(user_value_list)  # On Python 2.7, convert unicode to utf-8
            except ValueError:
                validation_error = "'%s' is not a valid string array" % str(user_value)
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error

            hashed_user_values = [sha256(encode_utf8(x), salt, context_salt) for x in user_value_list]
            if comparator == Comparator.ARRAY_CONTAINS_ANY_OF_HASHED:
                for comparison in comparison_value:
                    if comparison in hashed_user_values:
                        return True, error
            else:
                for comparison in comparison_value:
                    if comparison in hashed_user_values:
                        return False, None
                return True, error
        # EQUALS
        elif comparator == Comparator.EQUALS:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if user_value == comparison_value:
                return True, error
        # NOT EQUALS
        elif comparator == Comparator.NOT_EQUALS:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            if user_value != comparison_value:
                return True, error
        # STARTS WITH ANY OF, NOT STARTS WITH ANY OF, ENDS WITH ANY OF, NOT ENDS WITH ANY OF
        elif Comparator.STARTS_WITH_ANY_OF <= comparator <= Comparator.NOT_ENDS_WITH_ANY_OF:
            user_value = self._get_user_attribute_value_as_text(comparison_attribute, user_value, condition, key)
            for comparison in comparison_value:
                if (comparator == Comparator.STARTS_WITH_ANY_OF and user_value.startswith(comparison)) or \
                        (comparator == Comparator.ENDS_WITH_ANY_OF and user_value.endswith(comparison)):
                    return True, error
                elif (comparator == Comparator.NOT_STARTS_WITH_ANY_OF and user_value.startswith(comparison)) \
                        or (comparator == Comparator.NOT_ENDS_WITH_ANY_OF and user_value.endswith(comparison)):
                    return False, None

            # If no matches were found for the NOT_* conditions, then return True
            if comparator in [Comparator.NOT_STARTS_WITH_ANY_OF, Comparator.NOT_ENDS_WITH_ANY_OF]:
                return True, error
        # ARRAY CONTAINS ANY OF, ARRAY NOT CONTAINS ANY OF
        elif Comparator.ARRAY_CONTAINS_ANY_OF <= comparator <= Comparator.ARRAY_NOT_CONTAINS_ANY_OF:
            try:
                user_value_list = self._get_user_attribute_value_as_string_list(user_value)

                if sys.version_info[0] == 2:
                    user_value_list = unicode_to_utf8(user_value_list)  # On Python 2.7, convert unicode to utf-8
            except ValueError:
                validation_error = "'%s' is not a valid string array" % str(user_value)
                error = self._handle_invalid_user_attribute(comparison_attribute, comparator, comparison_value, key,
                                                            validation_error)
                return False, error

            if comparator == Comparator.ARRAY_CONTAINS_ANY_OF:
                for comparison in comparison_value:
                    if comparison in user_value_list:
                        return True, error
            else:
                for comparison in comparison_value:
                    if comparison in user_value_list:
                        return False, None
                return True, error

        return False, error
