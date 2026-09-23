import pygame


class GameController:
    AI_DELAY_MS = 700
    TRICK_PAUSE_MS = 1150

    def __init__(self, model, view):
        self.model = model
        self.view = view

        self.last_action_time = pygame.time.get_ticks()
        self.trick_complete_time = None

        # Local multiplayer privacy: a human must explicitly reveal their hand
        # each time control passes to them.
        self.revealed_player_index = None

        self.view.play_sound("shuffle")

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "menu"

        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return None

        if self.view.restart_rect.collidepoint(event.pos):
            self.model.new_game()
            self.revealed_player_index = None
            self.trick_complete_time = None
            self.last_action_time = pygame.time.get_ticks()
            self.view.play_sound("shuffle")
            return None

        if self.view.menu_rect.collidepoint(event.pos):
            return "menu"

        if self._needs_reveal():
            if self.view.reveal_rect.collidepoint(event.pos):
                self.revealed_player_index = self._active_human_index()
            return None

        if self.model.phase == "bidding":
            bidder = self.model.current_bidder

            if bidder.is_human:
                bid = self.view.get_clicked_bid(event.pos)

                if bid is not None:
                    previous_index = self.model.current_bidder_index

                    if self.model.submit_bid(previous_index, bid):
                        self.view.play_sound("bid")
                        self.last_action_time = pygame.time.get_ticks()
                        self._after_turn_change(previous_index)

            return None

        if self.model.phase == "playing":
            player = self.model.current_player

            if player.is_human and not self.model.trick_complete:
                card = self.view.get_clicked_card(event.pos)

                if card is not None:
                    previous_index = self.model.current_player_index

                    if self.model.play_card(previous_index, card):
                        self.view.play_sound("play")
                        self.last_action_time = pygame.time.get_ticks()
                        self._after_turn_change(previous_index)

                        if self.model.trick_complete:
                            self.trick_complete_time = pygame.time.get_ticks()
                            self.view.play_sound("trick")

            return None

        if self.model.phase == "hand_score":
            if self.view.next_hand_rect.collidepoint(event.pos):
                self.model.start_new_hand(rotate_dealer=True)
                self.revealed_player_index = None
                self.trick_complete_time = None
                self.last_action_time = pygame.time.get_ticks()
                self.view.play_sound("shuffle")

        return None

    def update(self):
        now = pygame.time.get_ticks()

        if self.model.phase == "bidding":
            bidder = self.model.current_bidder

            if not bidder.is_human and now - self.last_action_time >= self.AI_DELAY_MS:
                bid = bidder.choose_bid(self.model)
                previous_index = self.model.current_bidder_index

                if self.model.submit_bid(previous_index, bid):
                    self.view.play_sound("bid")
                    self.last_action_time = now
                    self._after_turn_change(previous_index)

            return

        if self.model.phase != "playing":
            return

        if self.model.trick_complete:
            if self.trick_complete_time is None:
                self.trick_complete_time = now

            if now - self.trick_complete_time >= self.TRICK_PAUSE_MS:
                previous_winner = self.model.pending_trick_winner
                self.model.finish_trick()
                self.trick_complete_time = None
                self.last_action_time = now
                self.revealed_player_index = None

                if self.model.phase == "game_over":
                    self.view.play_sound("game")

            return

        current = self.model.current_player

        if not current.is_human and now - self.last_action_time >= self.AI_DELAY_MS:
            valid = self.model.get_valid_cards()
            card = current.choose_card(self.model, valid)
            previous_index = self.model.current_player_index

            if card is not None and self.model.play_card(previous_index, card):
                self.view.play_sound("play")
                self.last_action_time = now
                self._after_turn_change(previous_index)

                if self.model.trick_complete:
                    self.trick_complete_time = now
                    self.view.play_sound("trick")

    def draw(self):
        self.view.draw(
            self.model,
            hand_revealed=not self._needs_reveal(),
        )

    def _active_human_index(self):
        if self.model.phase == "bidding":
            return self.model.current_bidder_index
        if self.model.phase == "playing":
            return self.model.current_player_index
        return None

    def _needs_reveal(self):
        active_index = self._active_human_index()
        if active_index is None:
            return False

        if not self.model.players[active_index].is_human:
            return False

        return self.revealed_player_index != active_index

    def _after_turn_change(self, previous_index):
        active_index = self._active_human_index()

        if active_index != previous_index:
            self.revealed_player_index = None
