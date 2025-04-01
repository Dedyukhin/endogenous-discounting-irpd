import random
import time
from otree.api import *  # Import oTree API

# Removed unused import of numpy for clarity

doc = """
This is a Block RT implementation of IRPD with endogenous continuation rule.
The game reads configuration parameters (such as payoffs, treatment type,
stop probabilities, block settings, and dice realizations) from a file.
"""


# ****************************************************************
# CONSTANTS AND GAME SETTINGS
# ****************************************************************
class C(BaseConstants):
    # Open the file with game parameters; each readline() extracts a parameter
    gameFile = open("IRPD_BlockRT/Random_realizations.txt", "r")

    NAME_IN_URL = 'irpd'
    PLAYERS_PER_GROUP = 2

    # Read payoff for both players cooperating from the file and convert to integer
    PayoffCC = int(gameFile.readline().split()[0])
    PayoffCD = 12  # Payoff when player cooperates and opponent defects
    PayoffDC = 50  # Payoff when player defects and opponent cooperates
    PayoffDD = 25  # Payoff when both defect

    # Read treatment parameter from the file
    Treatment = gameFile.readline().split()[0]

    # Stop probability parameters: determine the continuation rule
    StopProbability = 3
    StopProbabilityCC = int(gameFile.readline().split()[0])

    # Block settings: number of blocks and rounds per block
    num_blocks = int(gameFile.readline().split()[0])
    block_length = int(gameFile.readline().split()[0])

    # Dice realizations used for the continuation decision; convert each value to integer
    dice_realizations = [int(x) for x in gameFile.readline().split()]

    # Time limit configuration for the session
    time_limit = True
    time_limit_seconds = 30 * 60  # e.g., 60 seconds for the session if enabled

    # Total number of rounds in the experiment (blocks x rounds per block)
    NUM_ROUNDS = num_blocks * block_length


# ****************************************************************
# SUBSESSION, PLAYER, AND GROUP CLASSES
# ****************************************************************
class Subsession(BaseSubsession):
    # Currently no additional logic is needed at the subsession level.
    pass


class Player(BasePlayer):
    # Field for player's decision: 'C' for cooperate, 'D' for defect.
    decision = models.StringField(
        choices=['C', 'D'],
        widget=widgets.RadioSelect
    )
    # Optional field for player comments.
    comments = models.LongStringField(
        label="Please write anything you want here:",
        blank=True
    )

    # Game control flags and counters.
    terminated = models.BooleanField(initial=False)  # Flag to mark if current block/match ended.
    alive = models.BooleanField(initial=True)  # Flag indicating if player is active in the session.
    round = models.IntegerField(initial=1)  # Custom counter for round within a match.
    game_length = models.IntegerField(initial=0)  # Counter for rounds played in the current match.
    match = models.IntegerField(initial=1)  # Counter for the current match number.
    block = models.IntegerField(initial=1)  # Counter for the current block.
    potential_payoff = models.CurrencyField(initial=0)  # Accumulated payoff for the current match.

    def other_player(self):
        """
        Helper method to get the other player in the group.
        Assumes exactly two players per group.
        """
        return self.get_others_in_group()[0]


class Group(BaseGroup):
    # Field to store the dice roll result for determining match continuation.
    dice = models.IntegerField()
    # Field representing the stop probability threshold for the current round.
    probability = models.IntegerField()


# ****************************************************************
# PAGE CLASSES
# ****************************************************************

class Decision(Page):
    """
    Page where players choose their decision (cooperate or defect) and may leave comments.
    Also displays the history of previous decisions within the current match.
    """

    def is_displayed(player: Player):
        return player.alive

    form_model = 'player'
    form_fields = ['decision', 'comments']

    def is_displayed(player: Player):
        # Display this page only if the player is still active.
        return player.alive

    def vars_for_template(player: Player):
        # Build a history list of previous rounds in the current match.
        history = []
        if player.round_number > 1:
            for i in range(1, player.round_number):
                previous_player = player.in_round(i)
                # Include only rounds from the current match
                if previous_player.match == player.match:
                    history.append({
                        'round': previous_player.round,
                        # "1" represents cooperation ('C') and "2" represents defection ('D')
                        'my_choice': "1" if previous_player.decision == "C" else "2",
                        'other_choice': "1" if previous_player.other_player().decision == "C" else "2",
                    })
        return {'history': history,
                'Endogenous': C.Treatment == "Endo"}

    def before_next_page(player, timeout_happened):
        # On the very first round, record the session start time and initialize match length tracking.
        if player.round_number == 1:
            player.session.vars['start_time'] = time.time()
            player.participant.match_length = []


class ResultsWaitPage(WaitPage):
    """
    Wait page that processes players' decisions once both have submitted.
    Calculates payoffs and updates game state based on the players' choices.
    """

    def is_displayed(player: Player):
        return player.alive

    def after_all_players_arrive(group: Group):
        # Retrieve both players from the group.
        p1, p2 = group.get_players()

        # Determine payoffs and set the stop probability based on decisions.
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

        # Only update potential payoff and game length if neither player is terminated.
        if not p1.terminated and not p2.terminated:
            p1.potential_payoff += p1.payoff
            p2.potential_payoff += p2.payoff
            p1.game_length += 1
            p2.game_length += 1

        # Ensure probability is an integer.
        group.probability = int(group.probability)
        # Set the dice value based on the pre-generated dice realizations for this round.
        group.dice = C.dice_realizations[group.round_number - 1]


class EndRound(Page):
    """
    Page displayed at the end of each round showing results.
    It includes the choices made, the payoff for the round, and displays dice images.
    """

    @staticmethod
    def vars_for_template(player: Player):
        other_player = player.get_others_in_group()[0]
        # Generate a list of dice images up to the current probability threshold.
        needed = []
        for d in range(1, player.group.probability + 1):
            needed.append('images/dice-six-faces-' + str(d) + '.png')
        return {
            'my_decision': "1" if player.decision == 'C' else "2",
            'other_decision': "1" if other_player.decision == 'C' else "2",
            'payoff': player.payoff,
            'needed': needed
        }

    def is_displayed(player: Player):
        # Display this page only if the player is still active.
        return player.alive

    def before_next_page(player: Player, timeout_happened):
        # If the dice roll exceeds the threshold, mark the match as terminated.
        if player.group.dice > player.group.probability:
            player.terminated = True


class Wait(WaitPage):
    """
    Simple wait page that synchronizes all groups.
    """

    def is_displayed(player: Player):
        # Display this page only if the player is still active.
        return player.alive

    def after_all_players_arrive(group: Group):
        for player in group.get_players():
            # Propagate current match data to the next round if the game is still ongoing.
            if player.round_number < C.NUM_ROUNDS:
                next_round_player = player.in_round(player.round_number + 1)
                if next_round_player.round_number > 1:
                    next_round_player.match = player.match
                    next_round_player.block = player.block
                    next_round_player.round = player.round + 1
                    next_round_player.game_length = player.game_length
                    next_round_player.potential_payoff = player.potential_payoff

                # Update block counter if the current round is the last in the block.
                if player.subsession.round_number % C.block_length == 0:
                    next_round_player.block = player.block + 1

                # If the current match is terminated, update participant data accordingly.
                if player.terminated:
                    next_round_player.terminated = True


class WaitForAll(WaitPage):
    wait_for_all_groups = True

    def is_displayed(player: Player):
        # Display this page only if the player is still active.
        return player.alive


class EndBlock(Page):
    """
    Page displayed at the end of a block (after a fixed number of rounds).
    It shows block-specific results including dice outcomes and match summary.
    """

    def is_displayed(player: Player):
        # Only display this page at the end of each block.
        return (player.subsession.round_number % C.block_length == 0) and player.alive

    def vars_for_template(player: Player):
        history = []
        start = player.round_number - player.block * C.block_length + 1
        # Get the dice image for the starting round of the block.
        im = 'images/dice-six-faces-' + str(player.in_round(start).group.dice) + ".png"
        history = [{
            'round': player.in_round(start).round,
            # "1" represents cooperation ('C') and "2" represents defection ('D')
            'my_choice': "1" if player.in_round(start).decision == "C" else "2",
            'other_choice': "1" if player.in_round(start).other_player().decision == "C" else "2",
            'die': im
        }]
        # For each round in the block (except the first), append dice images if the round was not terminated.
        for r in range(player.round_number - player.block * C.block_length + 1, player.round_number):
            if not player.in_round(r).terminated:
                x = 'images/dice-six-faces-' + str(player.in_round(r + 1).group.dice) + ".png"
                history.append({
                    'round': player.in_round(r + 1).round,
                    # "1" represents cooperation ('C') and "2" represents defection ('D')
                    'my_choice': "1" if player.in_round(r + 1).decision == "C" else "2",
                    'other_choice': "1" if player.in_round(r + 1).other_player().decision == "C" else "2",
                    'die': x
                })
        return {
            'Ended': all(player.terminated for player in player.subsession.get_players()),
            'total_payoff': player.potential_payoff,
            'round_terminated': player.game_length,
            'history': history
        }

    def before_next_page(player: Player, timeout_happened):
        if player.round_number < C.NUM_ROUNDS:
            next_round_player = player.in_round(player.round_number + 1)
            if all(p.terminated for p in player.subsession.get_players()):
                next_round_player.participant.match_length.append(player.round)
                next_round_player.round = 1
                next_round_player.game_length = 0
                next_round_player.match += 1
                next_round_player.block = 1
                next_round_player.potential_payoff = 0
                next_round_player.terminated = False


class EndMatch(Page):
    """
    Page displayed at the end of a match (block boundary when all players are terminated).
    It shows the total payoff for the match.
    """

    def is_displayed(player: Player):
        return (player.subsession.round_number % C.block_length == 0 and
                all(player.terminated for player in player.subsession.get_players()) and
                player.alive)

    def vars_for_template(player: Player):
        return {'total_payoff': player.potential_payoff}

    # The following method is commented out. Uncomment to use time limit logic.
    # def before_next_page(player, timeout_happened):
    #     elapsed_time = time.time() - player.session.vars['start_time']
    #     if player.match == C.num_matches or (C.time_limit == True and elapsed_time > C.time_limit_seconds):
    #         player.alive = False


class RematchingWaitPage(WaitPage):
    """
    Wait page for rematching players between blocks.
    It checks for the end of the session based on rounds or time limits and then regroups players.
    """
    wait_for_all_groups = True

    def is_displayed(player: Player):
        # Display this page only if the player is still active.
        return player.alive

    def after_all_players_arrive(subsession: Subsession):
        # Calculate elapsed session time.
        elapsed_time = time.time() - subsession.session.vars['start_time']
        # Mark players as inactive if session is over or time limit exceeded.
        if (all(p.terminated for p in subsession.get_players()) and
                (subsession.round_number == C.NUM_ROUNDS or (C.time_limit and elapsed_time > C.time_limit_seconds))):
            for player in subsession.get_players():
                if player.terminated and (subsession.round_number % C.block_length == 0):
                    # Do not show any of remaining pages
                    for round_number in range(1, C.NUM_ROUNDS + 1):
                        player_in_round = player.in_round(round_number)
                        player_in_round.alive = False

        # If at the end of a block and all players are terminated, regroup for the next round.
        if (subsession.round_number % C.block_length == 0) and (
        all(player.terminated for player in subsession.get_players())):
            if subsession.round_number < C.NUM_ROUNDS:
                next_round = subsession.in_round(subsession.round_number + 1)
                next_round.group_randomly()
        else:
            next_round = subsession.in_round(subsession.round_number + 1)
            next_round.group_like_round(subsession.round_number)


class End(Page):
    """
    Final page displayed when the session ends (player is no longer active).
    Calculates the final payment based on a randomly selected match.
    """

    def is_displayed(player: Player):
        return player.alive == False

    def vars_for_template(player: Player):
        # Randomly select a match to determine the final payment.
        player.participant.payment_match = random.randint(1, player.match)
        # Find the round corresponding to the selected match and set the payment.
        for round_instance in player.in_all_rounds():
            if round_instance.match == player.participant.payment_match:
                payment = round_instance.potential_payoff
        player.participant.game_payment = payment
        player.participant.payoff = payment
        return {
            'payment': player.participant.payoff,
            'choosen_match': player.participant.payment_match,
        }

    # Optionally, specify the next app after this page by uncommenting below.
    def app_after_this_page(player: Player, upcoming_apps):
        return 'bret'


# ****************************************************************
# PAGE SEQUENCE
# ****************************************************************
page_sequence = [
    Decision,
    ResultsWaitPage,
    EndRound,
    Wait,
    WaitForAll,
    EndBlock,
    RematchingWaitPage,
    End
]