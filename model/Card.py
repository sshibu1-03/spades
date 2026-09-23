class Card:
    SUIT_SYMBOLS = {
        "Hearts": "♥",
        "Diamonds": "♦",
        "Clubs": "♣",
        "Spades": "♠",
    }

    RANK_VALUES = {
        "2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7,
        "8": 8, "9": 9, "10": 10, "J": 11, "Q": 12,
        "K": 13, "A": 14,
    }

    def __init__(self, suit, rank):
        self.suit = suit
        self.rank = rank

    @property
    def value(self):
        return self.RANK_VALUES[self.rank]

    @property
    def symbol(self):
        return self.SUIT_SYMBOLS[self.suit]

    @property
    def is_red(self):
        return self.suit in ("Hearts", "Diamonds")

    def __repr__(self):
        return f"{self.rank}{self.symbol}"

    def __eq__(self, other):
        return isinstance(other, Card) and self.suit == other.suit and self.rank == other.rank

    def __hash__(self):
        return hash((self.suit, self.rank))
