from otree.api import *
from PD import C as OriginalConstants

doc = """
Your app description
"""

class Constants(BaseConstants):
    name_in_url = 'quiz_with_explanations'
    players_per_group = None
    questions = [
        {"question": "True/False: The first entry in each cell represents your payoff, while the second entry represents the payoff of the person you are matched with.",
         "choices": ["True", "False"],
         "correct": "True",
         "explanation": "The first entry in each cell represents your payoff, while the second entry represents the payoff of the person you are matched with."},
        {"question": "True/False: The length of a match might depend on your actions",
         "choices": ["True", "False"],
         "correct": "True",
         "explanation": "If both you and a player you are matched with play action 1, then there is a 67% probability that game continues for a next round. Otherwise there is a 50% probability that game continues for the next round"},
        {"question": "If you choose Action 1 and the other person chooses Action 2, you will receive. . .",
         "choices": [str(OriginalConstants.PayoffCD), str(OriginalConstants.PayoffDD), str(OriginalConstants.PayoffCC), str(OriginalConstants.PayoffDC)],
         "correct": "12",
         "explanation": "In the payoff table, the top-right cell shows your payoff as the first entry, which is 12"},
        {"question": "If you have already played 2 rounds and you chose action 2, while the person you are matched with chose action 1, the probability that there will be another round in your match is. . .",
         "choices": ["25%", "50%", "67%", "90%"],
         "correct": "50%",
         "explanation": "If both you and a player you are matched with play action 1, then there is a 67% probability that game continues for a next round. Otherwise there is a 50% probability that game continues for the next round."},
    ]
    num_rounds = len(questions)

    PayoffCC = OriginalConstants.PayoffCC
    PayoffCD = OriginalConstants.PayoffCD
    PayoffDC = OriginalConstants.PayoffDC
    PayoffDD = OriginalConstants.PayoffDD
    StopProbability = OriginalConstants.StopProbability
    StopProbabilityCC = OriginalConstants.StopProbabilityCC

    time_limit = OriginalConstants.time_limit
    time_limit_seconds = OriginalConstants.time_limit_seconds

class Subsession(BaseSubsession):
    pass

class Group(BaseGroup):
    pass

class Player(BasePlayer):
    current_question = models.IntegerField(initial=0)  # Tracks the question index
    answer = models.StringField()
    is_correct = models.BooleanField()

from . import *

class question(Page):
    form_model = 'player'
    form_fields = ['answer']

    @staticmethod
    def vars_for_template(player: Player):
        question_data = Constants.questions[player.round_number - 1]
        return {
            'question': question_data['question'],
            'choices': question_data['choices'],
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        question_data = Constants.questions[player.round_number - 1]
        player.is_correct = player.answer == question_data['correct']

class explanation(Page):
    @staticmethod
    def vars_for_template(player: Player):
        question_data = Constants.questions[player.round_number - 1]
        return {
            'question': question_data['question'],
            'answer': player.answer,
            'is_correct': player.is_correct,
            'correct_answer': question_data['correct'],
            'explanation': question_data['explanation'],
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        player.current_question += 1

    @staticmethod
    def is_displayed(player: Player):
        return player.current_question < len(Constants.questions)

class Instructions_1(Page):
    def is_displayed(self):
        return self.subsession.round_number == 1

class Instructions_2(Page):
    def vars_for_template(self):
        continuation_chance = int(round(Constants.StopProbability / 6 * 100))
        return dict(continuation_chance=continuation_chance,
                    die_threshold= Constants.StopProbability,
                    die_threshold_plus_one = Constants.StopProbability + 1,
                    die_threshold_CC = Constants.StopProbabilityCC,
                    die_threshold_CC_plus_one = Constants.StopProbabilityCC + 1)

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
                    die_threshold_CC_plus_one=Constants.StopProbabilityCC + 1)

    def is_displayed(self):
        # Display only in the first round
        return self.round_number == Constants.num_rounds

class WaitForOthers(WaitPage):
    wait_for_all_groups = True  # Ensures synchronization across all groups
    def is_displayed(self):
        # Display only in the first round
        return self.round_number == Constants.num_rounds

page_sequence = [Instructions_1, Instructions_2, Instructions_3, question, explanation, after_quiz, WaitForOthers]
