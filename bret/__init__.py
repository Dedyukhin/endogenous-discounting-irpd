import random

from otree.api import *
from settings import LANGUAGE_CODE

author = 'Felix Holzmeister & Armin Pfurtscheller'
doc = """
Bomb Risk Elicitation Task (BRET) à la Crosetto/Filippin (2013), Journal of Risk and Uncertainty (47): 31-65.
"""


class C(BaseConstants):
    NAME_IN_URL = 'bret'
    PLAYERS_PER_GROUP = None
    RESULTS_1_ROUND_TEMPLATE = __name__ + '/results_1_round.html'
    RESULTS_MULTI_ROUND_TEMPLATE = __name__ + '/results_multi_round.html'
    # ---------------------------------------------------------------------------------------------------------------- #
    # --- Overall Settings and Appearance --- #
    # ---------------------------------------------------------------------------------------------------------------- #

    # value of single collected box
    # if the bomb is not collected, player's payoff per round is determined by <box_value> times <boxes_collected>
    # note that the currency of any earnings is determined by the oTree settings in settings.py
    # if you set this to a decimal number, you must set POINTS_DECIMAL_PLACES in settings.py
    BOX_VALUE = 1

    # number of rows and columns
    # i.e. the total number of boxes is determined by <num_rows> times <num_cols>
    NUM_ROWS = 10
    NUM_COLS = 10

    # box height and box width in pixels
    # make sure that the size of the boxes fits the screen of the device
    # note that the layout is responsive, i.e. boxes will break into new rows if they don't fit
    BOX_HEIGHT = '50px'
    BOX_WIDTH = '50px'

    # number of rounds to be played
    NUM_ROUNDS = 1

    # determines whether all rounds played are payed-off or whether one round is randomly chosen for payment
    # if <random_payoff = True>, one round is randomly determined for payment
    # if <random_payoff = False>, the final payoff of the task is the last round played
    # note that this is only of interest for the case of <num_rounds> larger than 1
    RANDOM_PAYOFF = True

    # if <instructions = True>, a separate template "Instructions_1.html" is rendered prior to the task in round 1
    # if <instructions = False>, the task starts immediately (e.g. in case of printed instructions)
    INSTRUCTIONS = True

    # show feedback by resolving boxes, i.e. toggle boxes and show whether bomb was collected or not
    # if <feedback = True>, the button "Solve" will be rendered and active after game play ends ("Stop")
    # if <feedback = False>, the button "Solve" won't be rendered such that no feedback about game outcome is provided
    FEEDBACK = True

    # show results page summarizing the game outcome
    # if <results = True>, a separate page containing all relevant information is displayed after finishing the task
    # if <num_rounds> larger than 1, results are summarized in a table and only shown after all rounds have been played
    RESULTS = True

    # ---------------------------------------------------------------------------------------------------------------- #
    # --- Settings Determining Game Play --- #
    # ---------------------------------------------------------------------------------------------------------------- #

    # "dynamic" or "static" game play
    # if <dynamic = True>, one box per time interval is collected automatically
    # in case of <dynamic = True>, game play is affected by the variables <time_interval> and <random> below
    # if <dynamic = False>, subjects collect as many boxes as they want by clicking or entering the respective number
    # in case of <dynamic = False>, game play is affected by the variables <random>, <devils_game> and <undoable>
    DYNAMIC = True

    # time interval between single boxes being collected (in seconds)
    # note that this only affects game play if <dynamic = True>
    TIME_INTERVAL = 2

    # collect boxes randomly or systematically
    # if <random = False>, boxes are collected row-wise one-by-one, starting in the top-left corner
    # if <random = True>, boxes are collected randomly (Fisher-Yates Algorithm)
    # note that this affects game play in both cases, <dynamic = True> and <dynamic = False>
    RANDOM = False

    # determines whether static game play allows for selecting boxes by clicking or by entering a number
    # if <devils_game = True>, game play is similar to Slovic (1965), i.e. boxes are collected by subjects
    # if <devils_game = False>, subjects enter the number of boxes they want to collect
    # note that this only affects game play if <dynamic = False>
    DEVILS_GAME = False

    # determine whether boxes can be toggled only once or as often as clicked
    # if <undoable = True> boxes can be selected and de-selected indefinitely often
    # if <undoable = False> boxes can be selected only once (i.e. decisions can not be undone)
    # note that this only affects game play if <dynamic = False> and <devils_game = True>
    UNDOABLE = True
    NUM_BOXES = NUM_ROWS * NUM_COLS


if LANGUAGE_CODE == 'de':
    from .lexicon_de import Lexicon
else:
    from .lexicon_en import Lexicon

which_language = {'en': False, 'de': False}  # noqa
which_language[LANGUAGE_CODE] = True


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    # whether bomb is collected or not
    # store as integer because it's easier for interop with JS
    bomb = models.IntegerField()
    bomb_row = models.IntegerField()
    bomb_col = models.IntegerField()
    boxes_collected = models.IntegerField()
    pay_this_round = models.BooleanField()
    round_result = models.CurrencyField()


# FUNCTIONS
def set_payoff(player: Player):
    participant = player.participant
    round_number = player.round_number

    # determine round_result as (potential) payoff per round
    if player.bomb:
        player.round_result = cu(0)
    else:
        player.round_result = player.boxes_collected * C.BOX_VALUE
    if round_number == 1:
        participant.vars['round_to_pay'] = C.NUM_ROUNDS # Corrected here such that last round is paid
    if C.RANDOM_PAYOFF:
        if round_number == participant.vars['round_to_pay']:
            player.pay_this_round = True
            player.payoff = player.round_result
        else:
            player.pay_this_round = False
            player.payoff = cu(0)
    else:
        player.payoff = player.round_result


class Instructions(Page):
    @staticmethod
    def is_displayed(player: Player):
        return C.INSTRUCTIONS and player.round_number == 1

    @staticmethod
    def vars_for_template(player: Player):
        return dict(num_nobomb=C.NUM_BOXES - 1, Lexicon=Lexicon, **which_language,)


class Game(Page):
    # form fields on player level
    form_model = 'player'
    form_fields = [
        'bomb',
        'boxes_collected',
        'bomb_row',
        'bomb_col',
    ]

    @staticmethod
    def vars_for_template(player: Player):
        return dict(Lexicon=Lexicon, **which_language)

    @staticmethod
    def js_vars(player: Player):
        participant = player.participant
        reset = participant.vars.pop('reset', True)
        if C.DYNAMIC:
            show_input = False
        else:
            show_input = not C.DEVILS_GAME
        return dict(
            reset=reset,
            show_input=show_input,
            NUM_ROWS=C.NUM_ROWS,
            NUM_COLS=C.NUM_COLS,
            BOX_HEIGHT=C.BOX_HEIGHT,
            BOX_WIDTH=C.BOX_WIDTH,
            FEEDBACK=C.FEEDBACK,
            RESULTS=C.RESULTS,
            DYNAMIC=C.DYNAMIC,
            TIME_INTERVAL=C.TIME_INTERVAL,
            RANDOM=C.RANDOM,
            UNDOABLE=C.UNDOABLE,
        )

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.participant.vars['reset'] = True
        set_payoff(player)


class Results(Page):
    @staticmethod
    def is_displayed(player: Player):
        return C.RESULTS and player.round_number == C.NUM_ROUNDS

    @staticmethod
    def vars_for_template(player: Player):
        participant = player.participant
        # total_payoff = sum([p.payoff for p in player.in_all_rounds()])
        if player.round_number == C.NUM_ROUNDS:
            total_payoff = player.payoff
            player.participant.bret_payoff = total_payoff
            player.participant.payoff += player.participant.bret_payoff
        return dict(
            player_in_all_rounds=player.in_all_rounds(),
            box_value=C.BOX_VALUE,
            boxes_collected=player.boxes_collected,
            bomb=player.bomb,
            bomb_row=player.bomb_row,
            bomb_col=player.bomb_col,
            round_result=player.round_result,
            round_to_pay=participant.vars['round_to_pay'],
            payoff=player.payoff,
            total_payoff=total_payoff,
            Lexicon=Lexicon,
            **which_language,
        )

class PracticeRound(Page):
    def is_displayed(player: Player):
        return C.RESULTS and player.round_number != C.NUM_ROUNDS

    def vars_for_template(player: Player):
        return dict(
            player_in_all_rounds=player.in_all_rounds(),
            box_value=C.BOX_VALUE,
            boxes_collected=player.boxes_collected,
            bomb=player.bomb,
            bomb_row=player.bomb_row,
            bomb_col=player.bomb_col,
            round_result=player.round_result,
            payoff=player.payoff,
            Lexicon=Lexicon,
            **which_language,
        )

class Wait(WaitPage):
    Wait_for_all_groups = True

page_sequence = [Wait, Instructions, Wait, Game, PracticeRound, Results]
