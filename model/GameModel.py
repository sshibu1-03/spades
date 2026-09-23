import random

from model.Deck import Deck
from model.Player import Player
from model.AIPlayer import AIPlayer
from model.Team import Team


class GameModel:
    PLAYER_COUNT = 4
    TRUMP_SUIT = "Spades"
    TARGET_SCORE = 500
    BAG_LIMIT = 10
    BAG_PENALTY = 100

    # University of Chicago rule used by default:
    # tricks taken by a failed Nil bidder do not help partner's contract
    # and do not become bags.
    NIL_TRICKS_COUNT_AS_BAGS = False

    def __init__(self, human_count=1):
        self.human_count = max(1, min(4, human_count))

        self.players = []
        for seat in range(self.PLAYER_COUNT):
            if seat < self.human_count:
                self.players.append(Player(f"Player {seat + 1}", seat, is_human=True))
            else:
                self.players.append(AIPlayer(f"Computer {seat + 1}", seat))

        self.teams = [
            Team("Team 1", (0, 2)),
            Team("Team 2", (1, 3)),
        ]

        self.dealer_index = random.randrange(self.PLAYER_COUNT)
        self.current_player_index = 0
        self.current_bidder_index = 0

        self.phase = "bidding"
        self.current_trick = []
        self.lead_suit = None
        self.spades_broken = False
        self.played_cards = []

        self.trick_complete = False
        self.pending_trick_winner = None
        self.tricks_completed = 0

        self.hand_number = 0
        self.hand_score_details = []
        self.status_message = ""
        self.game_winner_text = ""

        self.new_game()

    @property
    def current_player(self):
        return self.players[self.current_player_index]

    @property
    def current_bidder(self):
        return self.players[self.current_bidder_index]

    def new_game(self):
        for team in self.teams:
            team.reset_game()

        self.dealer_index = random.randrange(self.PLAYER_COUNT)
        self.hand_number = 0
        self.game_winner_text = ""
        self.start_new_hand(rotate_dealer=False)

    def start_new_hand(self, rotate_dealer=True):
        if rotate_dealer:
            self.dealer_index = (self.dealer_index + 1) % self.PLAYER_COUNT

        self.hand_number += 1

        deck = Deck()
        deck.shuffle()
        hands = deck.deal(self.dealer_index, self.PLAYER_COUNT)

        for player, hand in zip(self.players, hands):
            player.reset_for_hand(hand)

        self.phase = "bidding"
        self.current_bidder_index = (self.dealer_index + 1) % self.PLAYER_COUNT
        self.current_player_index = self.current_bidder_index

        self.current_trick = []
        self.lead_suit = None
        self.spades_broken = False
        self.played_cards = []
        self.trick_complete = False
        self.pending_trick_winner = None
        self.tricks_completed = 0
        self.hand_score_details = []

        self.status_message = f"{self.current_bidder.name} bids first."

    def submit_bid(self, player_index, bid):
        if self.phase != "bidding":
            return False

        if player_index != self.current_bidder_index:
            return False

        if not isinstance(bid, int) or bid < 0 or bid > 13:
            return False

        self.players[player_index].bid = bid

        if all(player.bid is not None for player in self.players):
            self.phase = "playing"
            self.current_player_index = (self.dealer_index + 1) % self.PLAYER_COUNT
            self.status_message = f"{self.current_player.name} leads the first trick."
        else:
            self.current_bidder_index = (self.current_bidder_index + 1) % self.PLAYER_COUNT
            self.current_player_index = self.current_bidder_index
            self.status_message = f"{self.current_bidder.name}'s bid."

        return True

    def team_index_for_player(self, player_index):
        return 0 if player_index in self.teams[0].player_indices else 1

    def partner_index(self, player_index):
        return (player_index + 2) % self.PLAYER_COUNT

    def team_bid(self, team_index):
        total = 0
        for player_index in self.teams[team_index].player_indices:
            bid = self.players[player_index].bid
            if bid is not None and bid > 0:
                total += bid
        return total

    def team_contract_tricks(self, team_index):
        """
        Tricks that count toward the non-Nil partnership contract.
        A Nil bidder's tricks are excluded.
        """
        total = 0
        for player_index in self.teams[team_index].player_indices:
            player = self.players[player_index]
            if not player.is_nil:
                total += player.tricks_won
        return total

    def team_tricks_needed(self, team_index):
        return max(
            0,
            self.team_bid(team_index) - self.team_contract_tricks(team_index),
        )

    def get_valid_cards(self, player_index=None):
        if self.phase != "playing" or self.trick_complete:
            return []

        if player_index is None:
            player_index = self.current_player_index

        player = self.players[player_index]
        valid = player.valid_cards(self.lead_suit)

        # Spades may not be led until broken unless the leader has only Spades.
        if self.lead_suit is None and not self.spades_broken:
            non_spades = [card for card in valid if card.suit != self.TRUMP_SUIT]
            if non_spades:
                valid = non_spades

        return valid

    def play_card(self, player_index, card):
        if self.phase != "playing" or self.trick_complete:
            return False

        if player_index != self.current_player_index:
            return False

        valid_cards = self.get_valid_cards(player_index)

        if card not in valid_cards:
            if self.lead_suit and self.players[player_index].has_suit(self.lead_suit):
                self.status_message = f"You must follow {self.lead_suit}."
            else:
                self.status_message = "That card cannot be led right now."
            return False

        player = self.players[player_index]
        player.remove_card(card)

        if not self.current_trick:
            self.lead_suit = card.suit

        # A Spade played while another suit was led breaks Spades.
        # Leading Spades because only Spades remain also breaks them.
        if card.suit == self.TRUMP_SUIT:
            if self.lead_suit != self.TRUMP_SUIT or not self.spades_broken:
                self.spades_broken = True

        self.current_trick.append((player_index, card))
        self.played_cards.append(card)

        if len(self.current_trick) == self.PLAYER_COUNT:
            self.trick_complete = True
            self.pending_trick_winner = self.current_trick_winner_index()
            winner = self.players[self.pending_trick_winner]
            self.status_message = f"{winner.name} wins the trick."
        else:
            self.current_player_index = (self.current_player_index + 1) % self.PLAYER_COUNT
            self.status_message = f"{self.current_player.name}'s turn."

        return True

    def current_trick_winner_index(self):
        if not self.current_trick:
            return None

        lead_suit = self.current_trick[0][1].suit
        winner_index, winning_card = self.current_trick[0]

        for player_index, card in self.current_trick[1:]:
            if self._beats(card, winning_card, lead_suit):
                winner_index = player_index
                winning_card = card

        return winner_index

    def card_would_win(self, card, player_index):
        test_trick = list(self.current_trick)
        test_trick.append((player_index, card))

        lead_suit = test_trick[0][1].suit
        winner_index, winning_card = test_trick[0]

        for index, test_card in test_trick[1:]:
            if self._beats(test_card, winning_card, lead_suit):
                winner_index = index
                winning_card = test_card

        return winner_index == player_index

    def _beats(self, challenger, current_best, lead_suit):
        if challenger.suit == current_best.suit:
            return challenger.value > current_best.value

        if challenger.suit == self.TRUMP_SUIT and current_best.suit != self.TRUMP_SUIT:
            return True

        if current_best.suit == self.TRUMP_SUIT:
            return False

        return challenger.suit == lead_suit and current_best.suit != lead_suit

    def finish_trick(self):
        if not self.trick_complete:
            return

        winner_index = self.pending_trick_winner
        self.players[winner_index].tricks_won += 1
        self.tricks_completed += 1

        self.current_trick = []
        self.lead_suit = None
        self.trick_complete = False
        self.pending_trick_winner = None

        if self.tricks_completed >= 13:
            self._score_hand()
            return

        self.current_player_index = winner_index
        self.status_message = f"{self.current_player.name} leads the next trick."

    def _score_hand(self):
        self.hand_score_details = []

        for team_index, team in enumerate(self.teams):
            team_bid = self.team_bid(team_index)
            contract_tricks = self.team_contract_tricks(team_index)

            delta = 0
            hand_bags = 0
            made_contract = contract_tricks >= team_bid

            # Partnership contract scoring.
            if team_bid > 0:
                if made_contract:
                    delta += team_bid * 10
                    hand_bags = max(0, contract_tricks - team_bid)
                    delta += hand_bags
                else:
                    delta -= team_bid * 10

            # Nil scoring is individual but applied to the team.
            nil_notes = []
            for player_index in team.player_indices:
                player = self.players[player_index]

                if player.is_nil:
                    if player.tricks_won == 0:
                        delta += 100
                        nil_notes.append(f"{player.name} made Nil (+100)")
                    else:
                        delta -= 100
                        nil_notes.append(f"{player.name} missed Nil (-100)")

                        if self.NIL_TRICKS_COUNT_AS_BAGS and made_contract:
                            hand_bags += player.tricks_won
                            delta += player.tricks_won

            previous_bags = team.bags
            team.bags += hand_bags

            bag_penalties = team.bags // self.BAG_LIMIT
            if bag_penalties:
                delta -= bag_penalties * self.BAG_PENALTY
                team.bags %= self.BAG_LIMIT

            team.score += delta

            self.hand_score_details.append({
                "team": team.name,
                "bid": team_bid,
                "contract_tricks": contract_tricks,
                "actual_team_tricks": sum(
                    self.players[i].tricks_won for i in team.player_indices
                ),
                "made_contract": made_contract,
                "hand_bags": hand_bags,
                "bags_before": previous_bags,
                "bags_after": team.bags,
                "bag_penalties": bag_penalties,
                "nil_notes": nil_notes,
                "delta": delta,
                "score": team.score,
            })

        winner = self._check_game_winner()

        if winner is not None:
            self.phase = "game_over"
            self.game_winner_text = (
                f"{self.teams[winner].name} wins "
                f"{self.teams[winner].score} to {self.teams[1 - winner].score}!"
            )
            self.status_message = self.game_winner_text
        else:
            self.phase = "hand_score"
            self.status_message = f"Hand {self.hand_number} complete."

    def _check_game_winner(self):
        reached = [
            index
            for index, team in enumerate(self.teams)
            if team.score >= self.TARGET_SCORE
        ]

        if not reached:
            return None

        if len(reached) == 1:
            return reached[0]

        if self.teams[0].score == self.teams[1].score:
            return None

        return 0 if self.teams[0].score > self.teams[1].score else 1
