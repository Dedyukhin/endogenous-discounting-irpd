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
    pass


# PAGES
class MyPage(Page):
    def vars_for_template(player):
        return {
            'payment_for_game': player.participant.game_payment.to_real_world_currency(player.session),
            'choosen_match': player.participant.payment_match,
            'risk_payment': player.participant.bret_payoff.to_real_world_currency(player.session),
            'EXPERIMENT_PAYMENT': player.participant.payoff_plus_participation_fee().to_real_world_currency(player.session)
        }


class ResultsWaitPage(WaitPage):
    pass


class Results(Page):
    pass


page_sequence = [MyPage]
