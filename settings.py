from os import environ

SESSION_CONFIGS = [
    dict(
        name = 'WCDC',
        app_sequence = ["Instructions_BRT", "IRPD_BlockRT", "bret", "Final"],  ##
        num_demo_participants = 2,
        display_name = 'When Cooperation Drives Continuation',
    ),
]

ROOMS = [
    {
        'name': 'room',
        'display_name': 'WCDC session',
        'participant_label_file': '_rooms/room.txt',  # optional
    },
    # you can add more rooms here
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.15, participation_fee=5.00, doc=""
)

PARTICIPANT_FIELDS = ['payment_match', 'match_length', 'game_payment', 'bret_payoff']
SESSION_FIELDS = []

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = 'en'

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = 'USD'
USE_POINTS = True

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = 'dedyukhin'

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = '1854410151345'
