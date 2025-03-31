from otree.api import *


doc = """
Your app description
"""


class C(BaseConstants):
    NAME_IN_URL = 'Final'
    PLAYERS_PER_GROUP = None
    NUM_ROUNDS = 1


class Subsession(BaseSubsession):
    pass


class Group(BaseGroup):
    pass


class Player(BasePlayer):
    age = models.IntegerField(label="What is your age?", min=18, max=100)
    gender = models.StringField(
        choices=[("Male", "Male"), ("Female", "Female"), ("Other", "Other"),
                 ("Prefer not to say", "Prefer not to say")],
        label="What is your gender?",
        widget=widgets.RadioSelect,
    )
    STEM = models.StringField(
        choices=[
            ("Yes", "Yes"),
            ("No", "No"),
            ("Prefer not to say", "Prefer not to say")
        ],
        label="Are you a STEM major?",
        widget=widgets.RadioSelect,
    )
    Economics = models.StringField(
        choices=[
            ("Yes", "Yes"),
            ("No", "No"),
            ("Prefer not to say", "Prefer not to say")
        ],
        label="Have you ever had an Economics class?",
        widget=widgets.RadioSelect,
    )
    comments = models.LongStringField(
        blank=True, label="Please feel free to provide reasoning of your choices in the experiment"
    )
    exp_comments = models.LongStringField(
        blank=True, label="Please feel free to provide comments regarding this experiment"
    )

import math
# PAGES
class MyPage(Page):
    def vars_for_template(player: Player):
        # amount = float(player.participant.payoff.to_real_world_currency(player.session))
        # player.participant.payoff = cu((math.ceil(amount * 4) / 4) / player.session.config['real_world_currency_per_point'])
        return {
            'payment_for_game': player.participant.game_payment.to_real_world_currency(player.session),
            'choosen_match': player.participant.payment_match,
            'risk_payment': player.participant.bret_payoff.to_real_world_currency(player.session),
            'EXPERIMENT_PAYMENT': player.participant.payoff.to_real_world_currency(player.session),
            'amount': player.participant.payoff
        }


class ResultsWaitPage(WaitPage):
    pass


class Demographics(Page):
    form_model = "player"
    form_fields = ["age", "gender", "STEM", "Economics", "comments", "exp_comments"]
        # age, gender, STEM major, Economic, Reasoning your actions

page_sequence = [Demographics, MyPage]
