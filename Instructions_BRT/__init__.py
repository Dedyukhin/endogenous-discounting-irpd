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
        {"question": "4. If you have already played 2 rounds and you chose 2, while the person you are matched with chose 1, for which die values will the game continue?",
         "choices": ["1,2,5,6", "1,2,3", "3,4,5,6", "1,2,3,4"],
         "correct": "1,2,3",
         "explanation": "To determine whether the match will continue for at least one more round, the computer will roll a six-sided die. If your choice in the previous round was 1 and the other person's choice was also 1, the match will continue for an additional round if the die lands on a 1, 2, 3, or 4. The match will end if the die lands on a 5 or 6. Otherwise, the match will continue for an additional round if the die lands on a 1, 2, or 3. The match will end if the die lands on a 4, 5, or 6."},
    ]
    num_rounds = len(questions)

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
    current_question = models.IntegerField(initial=10)  # Tracks the question index
    answer = models.StringField()
    is_correct = models.BooleanField(initial=True)

from . import *

class Question(Page):
    form_model = 'player'
    form_fields = ['answer']

    @staticmethod
    def vars_for_template(player: Player):
        if player.round_number == 1:
            player.current_question = 0

        question_data = Constants.questions[player.current_question]
        return {
            'question': question_data['question'][2:],
            'number': question_data['question'][0],
            'choices': question_data['choices'],
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        question_data = Constants.questions[player.current_question]
        player.is_correct = player.answer == question_data['correct']

    def error_message(player: Player, values):
        # Get the current question's data
        question_data = Constants.questions[player.current_question]
        # Check if the submitted answer matches the correct answer.
        if values['answer'] != question_data['correct']:
            return "Your answer is incorrect. Please try again."

    def is_displayed(player: Player):
        if player.round_number == 1:
            return True
        else:
            return player.current_question < len(Constants.questions)

class Explanation(Page):
    @staticmethod
    def vars_for_template(player: Player):
        question_data = Constants.questions[player.current_question]

        return {
            'question': question_data['question'][2:],
            'number': question_data['question'][0],
            'answer': player.answer,
            'is_correct': player.is_correct,
            'correct_answer': question_data['correct'],
            'explanation': question_data['explanation'],
        }

    @staticmethod
    def before_next_page(player: Player, timeout_happened):
        if player.round_number < Constants.num_rounds:
            player.in_round(player.round_number + 1).current_question = player.current_question + 1

    @staticmethod
    def is_displayed(player: Player):
        return player.current_question < len(Constants.questions)

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
                    die_threshold_CC_plus_one=Constants.StopProbabilityCC + 1)

    def is_displayed(self):
        return self.round_number == Constants.num_rounds

class WaitForOthers(WaitPage):
    wait_for_all_groups = True  # Ensures synchronization across all groups
    def is_displayed(self):
        # Display only in the first round
        return self.round_number == Constants.num_rounds

page_sequence = [Instructions_1, Instructions_2, Instructions_3, Question, Explanation, After_quiz, WaitForOthers]
