import random
from model.Card import Card


class Deck:
    SUITS = ["Clubs", "Diamonds", "Hearts", "Spades"]
    RANKS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]

    def __init__(self):
        self.cards = [
            Card(suit, rank)
            for suit in self.SUITS
            for rank in self.RANKS
        ]

    def shuffle(self):
        random.shuffle(self.cards)

    def deal(self, dealer_index, player_count=4):
        """Deal one at a time clockwise, beginning left of dealer."""
        hands = [[] for _ in range(player_count)]
        player_index = (dealer_index + 1) % player_count

        for card in self.cards:
            hands[player_index].append(card)
            player_index = (player_index + 1) % player_count

        return hands
