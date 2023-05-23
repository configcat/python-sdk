CONFIG_FILE_NAME = 'config_v6'

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
SEGMENT_RULES = 'r'  # Logically connected by AND

# Segment Rule (Comparison Rule)
COMPARISON_ATTRIBUTE = 'a'  # The attribute of the user object that should be used to evaluate this rule
COMPARATOR = 'c'

# Feature flag (Evaluation Formula)
SETTING_TYPE = 't'  # 0 = bool, 1 = string, 2 = int, 3 = double
PERCENTAGE_RULE_ATTRIBUTE = 'p'  # Percentage rule evaluation will hash this attribute of the User object to calculate the buckets.
TARGETING_RULES = 'r'  # Targeting Rules (Logically connected by OR)
VALUE = 'v'
VARIATION_ID = 'i'

# Targeting Rule (Evaluation Rule)
CONDITIONS = 'c'
SERVED_VALUE = 's'  # Value and Variation ID
PERCENTAGE_OPTIONS = 'p'

# Condition
COMPARISON_RULE = 't'
SEGMENT_CONDITION = 's'  # Segment targeting rule
DEPENDENT_FLAG_CONDITION = 'd'  # Prerequisite flag targeting rule

# Segment Condition
SEGMENT_INDEX = 's'
SEGMENT_COMPARATOR = 'c'

# Dependent Flag Condition
DEPENDENCY_SETTING_KEY = 'f'
DEPENDENCY_COMPARATOR = 'c'

# Percentage Option
PERCENTAGE = 'p'

# Value
BOOL_VALUE = 'b'
STRING_VALUE = 's'
INT_VALUE = 'i'
DOUBLE_VALUE = 'd'
STRING_LIST_VALUE = 'l'
