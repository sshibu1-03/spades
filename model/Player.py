class Player:
    SUIT_ORDER = {
        "Clubs": 0,
        "Diamonds": 1,
        "Hearts": 2,
        "Spades": 3,
    }

    def __init__(self, name, seat_index, is_human=True):
        self.name = name
        self.seat_index = seat_index
        self.is_human = is_human
        self.hand = []
        self.bid = None
        self.tricks_won = 0

    @property
    def is_nil(self):
        return self.bid == 0

    @property
    def partner_index(self):
        return (self.seat_index + 2) % 4

    def reset_for_hand(self, cards):
        self.hand = list(cards)
        self.bid = None
        self.tricks_won = 0
        self.sort_hand()

    def sort_hand(self):
        self.hand.sort(
            key=lambda card: (self.SUIT_ORDER[card.suit], card.value)
        )

    def valid_cards(self, lead_suit=None):
        if not self.hand:
            return []

        if lead_suit is None:
            return list(self.hand)

        matching = [card for card in self.hand if card.suit == lead_suit]
        return matching if matching else list(self.hand)

    def remove_card(self, card):
        self.hand.remove(card)

    def has_suit(self, suit):
        return any(card.suit == suit for card in self.hand)

    def suit_count(self, suit):
        return sum(1 for card in self.hand if card.suit == suit)
