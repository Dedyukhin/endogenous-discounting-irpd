from otree.api import *
from IRPD_BlockRT import C as OriginalConstants

doc = """
Your app description
"""

class Constants(BaseConstants):
    name_in_url = 'quiz_with_explanations'
    players_per_group = None
    questions = [
        {"question": "1. The first entry in each cell represents your payoff, while the second entry represents the payoff of the person you are matched with.",
         "choices": ["True", "False"],
         "correct": "True",
         "explanation": "The first entry in each cell represents your payoff, while the second entry represents the payoff of the person you are matched with."},
        {"question": "2. You will be paid for all matches.",
         "choices": ["True", "False"],
         "correct": "False",
         "explanation": "In this part, one match will be randomly selected to count toward your final payoff."},
        {"question": "3. If you choose 1 and the other person chooses 2, your payoff in this round will be:",
         "choices": [str(OriginalConstants.PayoffCD), str(OriginalConstants.PayoffDD), str(OriginalConstants.PayoffCC), str(OriginalConstants.PayoffDC)],
         "correct": "12",
         "explanation": "In the payoff table, the top-right cell shows your payoff as the first entry"},
        {"question": "4. You have already played 3 rounds and are now in round 4. In this round, you chose 2 and your opponent chose 1. Under which outcomes of the die roll does the game continue?",
         "choices": ["1,2,5,6", "1,2,3", "3,4,5,6", "1,2,3,4"],
         "correct": "1,2,3",
         "explanation": "To determine whether the match will continue for at least one more round, the computer will roll a six-sided die. If your choice in the previous round was 1 and the other person's choice was also 1, the match will continue for an additional round if the die lands on a 1, 2, 3, or 4. The match will end if the die lands on a 5 or 6. Otherwise, the match will continue for an additional round if the die lands on a 1, 2, or 3. The match will end if the die lands on a 4, 5, or 6."},
    ]
    num_rounds = 1

    PayoffCC = OriginalConstants.PayoffCC
    PayoffCD = OriginalConstants.PayoffCD
    PayoffDC = OriginalConstants.PayoffDC
    PayoffDD = OriginalConstants.PayoffDD
    StopProbability = OriginalConstants.StopProbability
    StopProbabilityCC = OriginalConstants.StopProbabilityCC

    Treatment = OriginalConstants.Treatment

    time_limit = OriginalConstants.time_limit
    time_limit_seconds = OriginalConstants.time_limit_seconds

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    is_correct = models.BooleanField(initial=True)

    quiz_q1 = models.BooleanField(
        label="1. The first entry in each cell represents your payoff, while the second entry represents the payoff of the person you are matched with.",
        choices=[
            ("True", True),
            ("False", False)],
        widget=widgets.RadioSelect,
        )
    quiz_q2 = models.BooleanField(
        label="2. You will be paid for all matches.",
        choices=[
            ("True", True),
            ("False", False)],
        widget=widgets.RadioSelect,
    )
    quiz_q3 = models.IntegerField(
        label="3. If you choose 1 and the other person chooses 2, your payoff in this round will be:", min=0, max=100
    )
    quiz_q4 = models.StringField(
        label="4. You have already played 3 rounds and are now in round 4. In this round, you chose 2 and your opponent chose 1. Under which outcomes of the die roll does the game continue?",
        choices=[("1,2,5,6", "1,2,5,6"),
                 ("1,2,3", "1,2,3"),
                 ("3,4,5,6", "3,4,5,6"),
                 ("1,2,3,4", "1,2,3,4")],
        widget=widgets.RadioSelect,
    )

from . import *

class Quiz(Page):
    form_model = 'player'
    form_fields = ['quiz_q1', 'quiz_q2','quiz_q3', 'quiz_q4']

    def vars_for_template(player: Player):
        return dict(Endogenous = Constants.Treatment == "Endo")

    def error_message(player: Player, values):
        # Let's check correctness of Q1 and Q2
        # If a question is answered incorrectly, return a string.
        # That string will be displayed at the top of the page as an error,
        # and oTree will not allow the participant to continue until they fix it.

        correct_answers = {
            'quiz_q1': True,
            'quiz_q2': False,
            'quiz_q3': OriginalConstants.PayoffCD,
            'quiz_q4': "1,2,3"
        }

        # We can accumulate errors:
        errors = []
        if values != correct_answers:
            player.is_correct = False
            return "You have at least one incorrect answer."

        if errors:
            # Return a single string joined by line breaks (or however you like)
            return " ".join(errors)
        # If we return None or empty, the participant can proceed

class Instructions_1(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1

class Instructions_2(Page):
    def vars_for_template(self):
        continuation_chance = int(round(Constants.StopProbability / 6 * 100))
        return dict(
            continuation_chance=continuation_chance,
            die_threshold= Constants.StopProbability,
            die_threshold_plus_one = Constants.StopProbability + 1,
            die_threshold_CC = Constants.StopProbabilityCC,
            die_threshold_CC_plus_one = Constants.StopProbabilityCC + 1,
            Endogenous = Constants.Treatment == "Endo")

    def is_displayed(self):
        return self.subsession.round_number == 1

class Instructions_3(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1

class After_quiz(Page):
    def vars_for_template(self):
        continuation_chance = int(round(Constants.StopProbability / 6 * 100))
        return dict(continuation_chance=continuation_chance,
                    die_threshold=Constants.StopProbability,
                    die_threshold_plus_one=Constants.StopProbability + 1,
                    die_threshold_CC=Constants.StopProbabilityCC,
                    die_threshold_CC_plus_one=Constants.StopProbabilityCC + 1,
                    Endogenous = Constants.Treatment == "Endo")
    def is_displayed(self):
        return self.round_number == Constants.num_rounds

class WaitForOthers(WaitPage):
    wait_for_all_groups = True  # Ensures synchronization across all groups
    def is_displayed(self):
        # Display only in the first round
        return self.round_number == Constants.num_rounds

page_sequence = [Instructions_1, Instructions_2, Instructions_3, Quiz, After_quiz, WaitForOthers]
