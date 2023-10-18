from configcatclient.constants import PREFERENCES, SALT, SEGMENTS, FEATURE_FLAGS, TARGETING_RULES, CONDITIONS, \
    SEGMENT_CONDITION, SEGMENT_INDEX, INLINE_SALT, INLINE_SEGMENT


def extend_config_with_inline_salt_and_segment(config):
    """
    Adds the inline salt and segment to the config.
    When using flag overrides, the original salt and segment indexes may become invalid. Therefore, we copy the
    object references to the locations where they are referenced and use these references instead of the indexes.
    """
    salt = config.get(PREFERENCES, {}).get(SALT, '')
    segments = config.get(SEGMENTS, [])
    settings = config.get(FEATURE_FLAGS, {})
    for setting in settings.values():
        if not isinstance(setting, dict):
            continue

        # add salt
        setting[INLINE_SALT] = salt

        # add segment to the segment conditions
        targeting_rules = setting.get(TARGETING_RULES, [])
        for targeting_rule in targeting_rules:
            conditions = targeting_rule.get(CONDITIONS, [])
            for condition in conditions:

                segment_condition = condition.get(SEGMENT_CONDITION)
                if segment_condition:
                    segment_index = segment_condition.get(SEGMENT_INDEX)
                    segment = segments[segment_index]
                    segment_condition[INLINE_SEGMENT] = segment
