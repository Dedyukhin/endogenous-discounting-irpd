import random
import time

from otree.api import *

import numpy as np
doc = """
"""


class C(BaseConstants):
    NAME_IN_URL = 'irpd'
    PLAYERS_PER_GROUP = 2
    PayoffCC = cu(4.8) # Or 32 for different treatment
    PayoffCD = cu(1.2)
    PayoffDC = cu(5)
    PayoffDD = cu(2.5)
    StopProbability = 3
    StopProbabilityCC = 4 # or 1/2 for other treatment

    time_limit = True
    time_limit_seconds = 60 # time limit for session (in seconds) since first round of first match (3600 in Dal Bo and Frechette AER 2011)

    num_matches = 10  # set to high number (e.g., 50) if time_limit == True
    NUM_ROUNDS = num_matches * 20

def creating_session(self):
    # Randomly regroup players after each round
    if self.round_number == 1:
        self.group_randomly()
    else:
        self.group_randomly()

class Subsession(BaseSubsession):
    def set_groups(self):
        players = self.get_players()
        unmatched = players[:]  # Copy list of players
        group_matrix = []

        while unmatched:
            player = unmatched.pop(0)  # Take the first unmatched player
            possible_partners = [
                p for p in unmatched if str(p.id) not in player.previous_partners.split(",")
            ]
            if possible_partners:
                partner = possible_partners.pop(0)  # Select the first available partner
                unmatched.remove(partner)
                group_matrix.append([player, partner])

                # Update the `previous_partners` field for both
                player.previous_partners += f",{partner.id}"
                partner.previous_partners += f",{player.id}"
            else:
                # If no valid partner found, pair randomly (handle edge cases)
                partner = unmatched.pop(0)
                group_matrix.append([player, partner])
                player.previous_partners += f",{partner.id}"
                partner.previous_partners += f",{player.id}"

        self.set_group_matrix(group_matrix)


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

    previous_partners = models.LongStringField(initial="")  # To store partner IDs as a strin

class Group(BaseGroup):
    number = models.IntegerField()
    probability = models.FloatField()

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

        if player.round_number > 1:
            prev_player = player.in_round(player.round_number - 1)
            player.match = prev_player.match
            player.round = prev_player.round + 1
            player.potential_payoff = prev_player.potential_payoff

            if prev_player.terminated:
                player.participant.match_length.append(prev_player.round)
                player.round = 1
                player.match += 1
                player.potential_payoff = 0

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
        import random
        group.number = random.randint(1, 6)

class EndRound(Page):
    @staticmethod
    def vars_for_template(player: Player):
        other_player = player.get_others_in_group()[0]
        return {
            'my_decision': player.decision,
            'other_decision': other_player.decision,
            'payoff': player.payoff,
        }

    def is_displayed(player: Player):
        return (player.terminated == False) and (player.alive == True)

    def before_next_page(player: Player, timeout_happened):
        if player.group.number > player.group.probability:
            player.terminated = True

class EndMatch(Page):
    def is_displayed(player: Player):
        return player.terminated and player.alive

    def vars_for_template(player: Player):
        total_payoff = sum([p.payoff for p in player.in_all_rounds()])
        return {
            'total_payoff': total_payoff,
        }
    def before_next_page(player, timeout_happened):
        elapsed_time = time.time() - player.session.vars['start_time']
        if player.match == C.num_matches or (C.time_limit == True and elapsed_time > C.time_limit_seconds):
            player.alive = False

class WaitForOthers(WaitPage):
    wait_for_all_groups = True  # Ensures synchronization across all groups
    def after_all_players_arrive(self):
        pass
class End(Page):
    def is_displayed(player: Player):
        return player.alive == False

    def vars_for_template(player: Player):
        player.participant.match_length.append(player.round)
        player.participant.payment_match = random.randint(1, player.match)
        m = player.participant.payment_match
        l = player.participant.match_length

        player.participant.payoff = player.in_round(sum(l[:m])).potential_payoff
        return {
            'payment': player.participant.payoff,
            'choosen_match': player.participant.payment_match,
        }

class WaitAfterEnd(WaitPage):
    def is_displayed(player: Player):
        return player.alive == False

    def app_after_this_page(player, upcoming_apps):
        return 'bret'

page_sequence = [Decision, ResultsWaitPage, EndRound,
                 EndMatch,
                 WaitForOthers, End, WaitAfterEnd, WaitForOthers]