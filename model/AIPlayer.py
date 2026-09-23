from model.Player import Player


class AIPlayer(Player):
    """
    Heuristic Spades AI.

    It is intentionally readable for a portfolio project:
    - estimates a bid from high cards, trump strength and suit length;
    - can choose Nil when the hand is unusually safe;
    - knows its partner;
    - tries to protect a Nil partner;
    - avoids wasting high cards when its partner already controls a trick;
    - uses the cheapest card that can win when the team needs tricks.
    """

    def __init__(self, name, seat_index):
        super().__init__(name, seat_index, is_human=False)

    def choose_bid(self, game):
        nil_risk = self._nil_risk()

        # Nil is attractive only when the hand is genuinely weak.
        # Avoid it when the partner has already bid Nil.
        partner = game.players[self.partner_index]
        partner_nil = partner.bid == 0

        if nil_risk <= 1.4 and not partner_nil:
            return 0

        estimate = 0.0
        counts = {
            suit: self.suit_count(suit)
            for suit in ("Clubs", "Diamonds", "Hearts", "Spades")
        }

        for card in self.hand:
            length = counts[card.suit]

            if card.rank == "A":
                estimate += 0.95
            elif card.rank == "K":
                estimate += 0.72 if length >= 2 else 0.48
            elif card.rank == "Q":
                estimate += 0.42 if length >= 3 else 0.20
            elif card.rank == "J":
                estimate += 0.16 if length >= 4 else 0.05

            if card.suit == "Spades":
                if card.rank in ("A", "K", "Q", "J"):
                    estimate += 0.35
                elif counts["Spades"] >= 5:
                    estimate += 0.20

        # Short side suits make low spades more useful for trumping.
        for suit in ("Clubs", "Diamonds", "Hearts"):
            if counts[suit] == 0:
                estimate += 0.65 * max(0, counts["Spades"] - 2)
            elif counts[suit] == 1:
                estimate += 0.28 * max(0, counts["Spades"] - 2)

        bid = int(round(estimate))
        bid = max(1, min(8, bid))

        # If partner has already bid aggressively, be a little conservative.
        if partner.bid is not None and partner.bid >= 5 and bid >= 3:
            bid -= 1

        return max(1, bid)

    def _nil_risk(self):
        risk = 0.0
        spades = self.suit_count("Spades")

        for card in self.hand:
            if card.rank == "A":
                risk += 4.0
            elif card.rank == "K":
                risk += 2.6
            elif card.rank == "Q":
                risk += 1.5
            elif card.rank == "J":
                risk += 0.8
            elif card.rank == "10":
                risk += 0.35

            if card.suit == "Spades":
                if card.value >= 11:
                    risk += 1.8
                elif card.value >= 9:
                    risk += 0.7

        if spades >= 4:
            risk += (spades - 3) * 1.0

        return risk

    def choose_card(self, game, valid_cards):
        if not valid_cards:
            return None

        # Nil bidders prioritize losing every trick.
        if self.is_nil:
            return self._choose_nil_card(game, valid_cards)

        partner = game.players[self.partner_index]

        # When leading, choose strategically rather than randomly.
        if not game.current_trick:
            return self._choose_lead(game, valid_cards)

        current_winner = game.current_trick_winner_index()
        partner_winning = current_winner == self.partner_index

        # Protect a partner who bid Nil: if partner is accidentally winning
        # the current trick, try to cover them by taking the trick.
        if partner.is_nil and partner.tricks_won == 0 and current_winner == self.partner_index:
            winners = [c for c in valid_cards if game.card_would_win(c, self.seat_index)]
            if winners:
                return self._cheapest_winner(game, winners)

        team_index = game.team_index_for_player(self.seat_index)
        team_needs = game.team_tricks_needed(team_index)

        # If partner is already winning and there is no Nil emergency,
        # preserve strength and play cheaply.
        if partner_winning:
            return self._lowest_expendable(valid_cards)

        winners = [c for c in valid_cards if game.card_would_win(c, self.seat_index)]

        # When the partnership still needs tricks, actively take affordable wins.
        if winners and team_needs > 0:
            return self._cheapest_winner(game, winners)

        # Near the end of the hand, take a win if it helps avoid being set.
        cards_left = sum(len(p.hand) for p in game.players)
        if winners and cards_left <= 16:
            return self._cheapest_winner(game, winners)

        # Otherwise dump risk while trying not to create unnecessary bags.
        return self._discard_card(valid_cards)

    def _choose_lead(self, game, valid_cards):
        partner = game.players[self.partner_index]

        # If partner is Nil, lead low cards from longer suits to give partner
        # room to duck underneath.
        if partner.is_nil and partner.tricks_won == 0:
            non_spades = [c for c in valid_cards if c.suit != "Spades"]
            pool = non_spades if non_spades else valid_cards
            return min(pool, key=lambda c: (self.suit_count(c.suit), c.value))

        # Prefer a likely winner when our team still needs tricks.
        team_index = game.team_index_for_player(self.seat_index)
        if game.team_tricks_needed(team_index) > 0:
            aces = [c for c in valid_cards if c.rank == "A"]
            if aces:
                return min(aces, key=lambda c: self.suit_count(c.suit))

            high_spades = [c for c in valid_cards if c.suit == "Spades" and c.value >= 12]
            if high_spades:
                return max(high_spades, key=lambda c: c.value)

        # Otherwise lead low from the longest non-spade suit.
        non_spades = [c for c in valid_cards if c.suit != "Spades"]
        pool = non_spades if non_spades else valid_cards

        suit_counts = {}
        for card in pool:
            suit_counts[card.suit] = suit_counts.get(card.suit, 0) + 1

        longest = max(suit_counts.values())
        preferred = [c for c in pool if suit_counts[c.suit] == longest]
        return min(preferred, key=lambda c: c.value)

    def _choose_nil_card(self, game, valid_cards):
        # Prefer cards that do not currently win the trick.
        if game.current_trick:
            losing = [
                card for card in valid_cards
                if not game.card_would_win(card, self.seat_index)
            ]
            if losing:
                # Shed the highest safe card first.
                return max(losing, key=lambda c: (c.suit == "Spades", c.value))

        # If forced to lead or forced to win, play the lowest-risk card.
        return min(valid_cards, key=lambda c: (c.suit == "Spades", c.value))

    @staticmethod
    def _lowest_expendable(cards):
        non_spades = [c for c in cards if c.suit != "Spades"]
        pool = non_spades if non_spades else cards
        return min(pool, key=lambda c: c.value)

    @staticmethod
    def _discard_card(cards):
        # If void in the led suit, throwing a dangerous high side-suit card
        # can reduce future accidental tricks. Preserve Spades when possible.
        non_spades = [c for c in cards if c.suit != "Spades"]
        if non_spades:
            return max(non_spades, key=lambda c: c.value)
        return min(cards, key=lambda c: c.value)

    @staticmethod
    def _cheapest_winner(game, cards):
        return min(
            cards,
            key=lambda c: (
                c.suit == game.TRUMP_SUIT,
                c.value,
            ),
        )
