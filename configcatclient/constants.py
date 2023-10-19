CONFIG_FILE_NAME = 'config_v6'
SERIALIZATION_FORMAT_VERSION = 'v2'

# Config
PREFERENCES = 'p'
SEGMENTS = 's'
FEATURE_FLAGS = 'f'

# Preferences
BASE_URL = 'u'
REDIRECT = 'r'
SALT = 's'

# Segment
SEGMENT_NAME = 'n'  # The first 4 characters of the Segment's name
SEGMENT_CONDITIONS = 'r'  # The list of segment rule conditions (has a logical AND relation between the items).

# Segment Condition (User Condition)
COMPARISON_ATTRIBUTE = 'a'  # The attribute of the user object that should be used to evaluate this rule
COMPARATOR = 'c'

# Feature flag (Evaluation Formula)
SETTING_TYPE = 't'  # 0 = bool, 1 = string, 2 = int, 3 = double
PERCENTAGE_RULE_ATTRIBUTE = 'a'  # Percentage rule evaluation hashes this attribute of the User object to calculate the buckets
TARGETING_RULES = 'r'  # Targeting Rules (Logically connected by OR)
PERCENTAGE_OPTIONS = 'p'  # Percentage Options without conditions
VALUE = 'v'
VARIATION_ID = 'i'
INLINE_SALT = 'inline_salt'

# Targeting Rule (Evaluation Rule)
CONDITIONS = 'c'
SERVED_VALUE = 's'  # Value and Variation ID
TARGETING_RULE_PERCENTAGE_OPTIONS = 'p'

# Condition
USER_CONDITION = 't'
SEGMENT_CONDITION = 's'  # Segment targeting rule
PREREQUISITE_FLAG_CONDITION = 'd'  # Prerequisite flag targeting rule

# Segment Condition
SEGMENT_INDEX = 's'
SEGMENT_COMPARATOR = 'c'
INLINE_SEGMENT = 'inline_segment'

# Prerequisite Flag Condition
PREREQUISITE_FLAG_KEY = 'f'
PREREQUISITE_COMPARATOR = 'c'

# Percentage Option
PERCENTAGE = 'p'

# Value
BOOL_VALUE = 'b'
STRING_VALUE = 's'
INT_VALUE = 'i'
DOUBLE_VALUE = 'd'
STRING_LIST_VALUE = 'l'
