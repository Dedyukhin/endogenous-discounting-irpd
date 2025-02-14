import random
import time

from otree.api import *

import numpy as np
doc = """
"""


class C(BaseConstants):
    NAME_IN_URL = 'irpd'
    PLAYERS_PER_GROUP = 2
    PayoffCC = 32 # Or 48 for different treatment
    PayoffCD = 12
    PayoffDC = 50
    PayoffDD = 25
    StopProbability = 3
    StopProbabilityCC = 4 # or 1/2 for other treatment

    time_limit = True
    time_limit_seconds = 10*60 # time limit for session (in seconds) since first round of first match (3600 in Dal Bo and Frechette AER 2011)

    num_matches = 30  # set to high number (e.g., 50) if time_limit == True
    NUM_ROUNDS = num_matches * 5

# def creating_session(self):
# #   Randomly regroup players after each round
#     if self.round_number == 1:
#         new_group_matrix = self.get_group_matrix()
#
#     if self.round_number > 1:
#         self.set_group_matrix(new_group_matrix)

class Subsession(BaseSubsession):
    pass

class Player(BasePlayer):
    decision = models.StringField(
        choices=['C', 'D'],
        widget=widgets.RadioSelect
    )
    comments = models.LongStringField(
        label="Please write anything you want here:",
        blank=True  # Allows the field to be optional
    )

    terminated = models.BooleanField(initial=False)
    alive = models.BooleanField(initial=True)  # Flag to terminate
    round = models.IntegerField(initial=1)
    match = models.IntegerField(initial=1)
    potential_payoff = models.CurrencyField(initial=0)

    def other_player(self):
        return self.get_others_in_group()[0]

class Group(BaseGroup):
    number = models.IntegerField()
    probability = models.IntegerField()

#############################################################################################
class Decision(Page):

    form_model = 'player'
    form_fields = ['decision', 'comments']

    def is_displayed(player: Player):
        return player.terminated == False and player.alive

    def before_next_page(player, timeout_happened):
        if player.round_number == 1:
            player.session.vars['start_time'] = time.time()
            player.participant.match_length = []

class ResultsWaitPage(WaitPage):
    def after_all_players_arrive(group: Group):
        p1, p2 = group.get_players()

        if p1.decision == 'C' and p2.decision == 'C':
            p1.payoff = C.PayoffCC
            p2.payoff = C.PayoffCC
            group.probability = C.StopProbabilityCC
        if p1.decision == 'C' and p2.decision == 'D':
            p1.payoff = C.PayoffCD
            p2.payoff = C.PayoffDC
            group.probability = C.StopProbability
        if p1.decision == 'D' and p2.decision == 'C':
            p1.payoff = C.PayoffDC
            p2.payoff = C.PayoffCD
            group.probability = C.StopProbability
        if p1.decision == 'D' and p2.decision == 'D':
            p1.payoff = C.PayoffDD
            p2.payoff = C.PayoffDD
            group.probability = C.StopProbability

        p1.potential_payoff += p1.payoff
        p2.potential_payoff += p2.payoff
        group.probability = int(group.probability)
        import random
        group.number = random.randint(1, 6)

class EndRound(Page):
    @staticmethod
    def vars_for_template(player: Player):
        other_player = player.get_others_in_group()[0]
        return {
            'my_decision': "1" if player.decision == 'C' else "2",
            'other_decision': "1" if other_player.decision == 'C' else "2",
            'payoff': player.payoff,
        }

    def is_displayed(player: Player):
        return (player.terminated == False) and (player.alive == True)

    def before_next_page(player: Player, timeout_happened):
        if player.group.number > player.group.probability:
            player.terminated = True

        next_round_player = player.in_round(player.round_number + 1)

        if next_round_player.round_number > 1:
            next_round_player.match = player.match
            next_round_player.round = player.round + 1
            next_round_player.potential_payoff = player.potential_payoff

        if player.terminated:
            next_round_player.participant.match_length.append(player.round)
            next_round_player.round = 1
            next_round_player.match += 1
            next_round_player.potential_payoff = 0

class EndMatch(Page):
    def is_displayed(player: Player):
        return player.terminated and player.alive

    def vars_for_template(player: Player):
        return {
            'total_payoff': player.potential_payoff,
        }
    def before_next_page(player, timeout_happened):
        elapsed_time = time.time() - player.session.vars['start_time']
        if player.match == C.num_matches or (C.time_limit == True and elapsed_time > C.time_limit_seconds):
            player.alive = False

class RematchingWaitPage(WaitPage):
    wait_for_all_groups = True

    def after_all_players_arrive(subsession: Subsession):
        # Collect players who need to be rematched
        players_to_rematch = [p for p in subsession.get_players() if p.terminated]
        random.shuffle(players_to_rematch)
        remaining_players = [p for p in subsession.get_players() if not p.terminated]

        # Create new groups
        new_group_matrix = []

        # Add rematched players to new groups
        while len(players_to_rematch) >= C.PLAYERS_PER_GROUP:
            if (players_to_rematch[0].other_player() == players_to_rematch[1]) and (len(players_to_rematch) > C.PLAYERS_PER_GROUP):
                new_group_matrix.append([players_to_rematch[0], players_to_rematch[2]])
                players_to_rematch = [players_to_rematch[1]] + players_to_rematch[3:]
            else:
                new_group_matrix.append(players_to_rematch[:2])
                players_to_rematch = players_to_rematch[2:]

        # Keep existing groups for remaining players
        for group in subsession.get_groups():
            group_players = group.get_players()
            if all(not p.terminated for p in group_players):
                new_group_matrix.append(group_players)

        # Set the new group matrix
        subsession.in_round(subsession.round_number + 1).set_group_matrix(new_group_matrix)

class End(Page):
    def is_displayed(player: Player):
        return player.alive == False

    def vars_for_template(player: Player):
        player.participant.match_length.append(player.round)
        player.participant.payment_match = random.randint(1, player.match)
        m = player.participant.payment_match
        l = player.participant.match_length

        player.participant.game_payment = player.in_round(sum(l[:m])).potential_payoff
        player.participant.payoff = player.in_round(sum(l[:m])).potential_payoff
        return {
            'payment': player.participant.payoff,
            'choosen_match': player.participant.payment_match,
        }

    def app_after_this_page(player, upcoming_apps):
        return 'bret'


page_sequence = [Decision, ResultsWaitPage, EndRound,
                 EndMatch,
                 RematchingWaitPage, End]
