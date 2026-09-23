from pathlib import Path
import pygame


class GameView:
    CARD_W = 76
    CARD_H = 108

    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.title_font = pygame.font.SysFont("georgia", 28, bold=True)
        self.heading_font = pygame.font.SysFont("arial", 25, bold=True)
        self.font = pygame.font.SysFont("arial", 19)
        self.small_font = pygame.font.SysFont("arial", 15)
        self.tiny_font = pygame.font.SysFont("arial", 13)
        self.card_font = pygame.font.SysFont("arial", 22, bold=True)
        self.suit_font = pygame.font.SysFont("segoeuisymbol", 34, bold=True)

        self.card_rects = []
        self.bid_rects = {}
        self.reveal_rect = pygame.Rect(self.width // 2 - 130, self.height // 2 + 40, 260, 52)
        self.next_hand_rect = pygame.Rect(self.width // 2 - 110, self.height - 110, 220, 48)
        self.restart_rect = pygame.Rect(self.width - 220, 18, 92, 36)
        self.menu_rect = pygame.Rect(self.width - 112, 18, 92, 36)

        self.assets_dir = Path(__file__).resolve().parent / "assets"
        self.sounds_dir = Path(__file__).resolve().parent / "sounds"

        self.card_back = self._load_image(
            self.assets_dir / "cards" / "card_back.png",
            (self.CARD_W, self.CARD_H),
        )
        self.table_texture = self._load_image(
            self.assets_dir / "backgrounds" / "table_texture.png",
            (self.width, self.height),
        )

        self.sounds = {}
        self._load_sounds()

    def _load_image(self, path, size):
        if not path.exists():
            return None

        try:
            image = pygame.image.load(str(path)).convert_alpha()
            return pygame.transform.smoothscale(image, size)
        except pygame.error:
            return None

    def _load_sounds(self):
        names = {
            "bid": "bid.wav",
            "play": "card_play.wav",
            "trick": "trick_win.wav",
            "shuffle": "shuffle.wav",
            "game": "game_win.wav",
        }

        for name, filename in names.items():
            path = self.sounds_dir / filename
            if path.exists():
                try:
                    self.sounds[name] = pygame.mixer.Sound(str(path))
                except pygame.error:
                    pass

    def play_sound(self, name):
        sound = self.sounds.get(name)
        if sound:
            sound.play()

    def draw(self, model, hand_revealed=True):
        if self.table_texture:
            self.screen.blit(self.table_texture, (0, 0))
        else:
            self.screen.fill((19, 86, 59))

        self._draw_table_border()
        self._draw_header(model)
        self._draw_team_scoreboards(model)
        self._draw_players(model, hand_revealed)

        if model.phase == "bidding":
            self._draw_bidding(model, hand_revealed)
        elif model.phase == "playing":
            self._draw_trick(model)
            self._draw_human_hand(model, hand_revealed)
        elif model.phase == "hand_score":
            self._draw_hand_score(model)
        elif model.phase == "game_over":
            self._draw_game_over(model)

        if self.needs_privacy_overlay(model, hand_revealed):
            self._draw_privacy_overlay(model)

    def _draw_table_border(self):
        pygame.draw.rect(
            self.screen,
            (166, 125, 66),
            pygame.Rect(7, 7, self.width - 14, self.height - 14),
            6,
            border_radius=24,
        )

    def _draw_header(self, model):
        title = self.title_font.render("♠ SPADES", True, (249, 241, 215))
        self.screen.blit(title, (24, 17))

        dealer = model.players[model.dealer_index].name
        details = self.small_font.render(
            f"Hand {model.hand_number}   •   Dealer: {dealer}   •   Target: {model.TARGET_SCORE}",
            True,
            (214, 229, 220),
        )
        self.screen.blit(details, (25, 55))

        if model.phase == "playing":
            broken = "Spades broken" if model.spades_broken else "Spades not broken"
            info = self.small_font.render(broken, True, (242, 215, 143))
            self.screen.blit(info, (25, 78))

        status = self.font.render(model.status_message, True, (250, 243, 220))
        self.screen.blit(
            status,
            status.get_rect(center=(self.width // 2, 34)),
        )

        self._draw_button(self.restart_rect, "Restart")
        self._draw_button(self.menu_rect, "Menu")

    def _draw_team_scoreboards(self, model):
        left = pygame.Rect(25, 112, 250, 78)
        right = pygame.Rect(self.width - 275, 112, 250, 78)

        for team_index, rect in enumerate((left, right)):
            team = model.teams[team_index]

            pygame.draw.rect(self.screen, (12, 60, 44), rect, border_radius=12)
            pygame.draw.rect(self.screen, (207, 182, 121), rect, 2, border_radius=12)

            title = self.font.render(
                f"{team.name}: {team.score}",
                True,
                (248, 239, 211),
            )
            bags = self.small_font.render(
                f"Bags: {team.bags}/10    Team bid: {model.team_bid(team_index)}",
                True,
                (207, 222, 214),
            )

            self.screen.blit(title, (rect.x + 14, rect.y + 13))
            self.screen.blit(bags, (rect.x + 14, rect.y + 46))

    def _draw_players(self, model, hand_revealed):
        positions = [
            (self.width // 2, self.height - 178),
            (125, self.height // 2 + 10),
            (self.width // 2, 150),
            (self.width - 125, self.height // 2 + 10),
        ]

        for index, player in enumerate(model.players):
            x, y = positions[index]

            active = (
                (model.phase == "bidding" and index == model.current_bidder_index)
                or (model.phase == "playing" and index == model.current_player_index)
            )

            color = (255, 222, 118) if active else (244, 244, 238)

            team_label = "Team 1" if index in (0, 2) else "Team 2"
            name = self.font.render(f"{player.name} • {team_label}", True, color)
            self.screen.blit(name, name.get_rect(center=(x, y)))

            bid_text = "—" if player.bid is None else ("Nil" if player.bid == 0 else str(player.bid))
            info = self.small_font.render(
                f"Bid: {bid_text}   Tricks: {player.tricks_won}   Cards: {len(player.hand)}",
                True,
                (212, 226, 218),
            )
            self.screen.blit(info, info.get_rect(center=(x, y + 24)))

            show_back = not (
                player.is_human
                and index == model.current_player_index
                and hand_revealed
                and model.phase in ("bidding", "playing")
            )

            if show_back and len(player.hand) > 0:
                self._draw_card_back_stack(x, y + 48, min(6, len(player.hand)))

    def _draw_card_back_stack(self, center_x, y, count):
        if count <= 0:
            return

        spacing = 11
        total_width = self.CARD_W + spacing * (count - 1)
        start_x = center_x - total_width // 2

        for i in range(count):
            rect = pygame.Rect(start_x + i * spacing, y, self.CARD_W, self.CARD_H)
            if self.card_back:
                self.screen.blit(self.card_back, rect)
            else:
                pygame.draw.rect(self.screen, (20, 42, 86), rect, border_radius=9)
                pygame.draw.rect(self.screen, (225, 232, 241), rect, 2, border_radius=9)
                inner = rect.inflate(-12, -12)
                pygame.draw.rect(self.screen, (46, 82, 139), inner, 2, border_radius=7)

    def _draw_bidding(self, model, hand_revealed):
        self.bid_rects = {}

        bidder = model.current_bidder
        if not bidder.is_human or not hand_revealed:
            return

        self._draw_hand_cards(bidder.hand, enabled_cards=set(bidder.hand), y=self.height - self.CARD_H - 22)

        panel = pygame.Rect(self.width // 2 - 340, 265, 680, 165)
        pygame.draw.rect(self.screen, (239, 234, 215), panel, border_radius=16)
        pygame.draw.rect(self.screen, (76, 63, 40), panel, 3, border_radius=16)

        heading = self.heading_font.render(
            f"{bidder.name}: How many tricks will you take?",
            True,
            (37, 46, 41),
        )
        self.screen.blit(
            heading,
            heading.get_rect(center=(self.width // 2, panel.y + 34)),
        )

        hint = self.small_font.render(
            "0 = Nil. Your bid combines with your partner's bid.",
            True,
            (75, 84, 79),
        )
        self.screen.blit(
            hint,
            hint.get_rect(center=(self.width // 2, panel.y + 65)),
        )

        start_x = panel.x + 35
        button_w = 41
        gap = 5
        y = panel.y + 93

        for bid in range(14):
            rect = pygame.Rect(start_x + bid * (button_w + gap), y, button_w, 42)
            self.bid_rects[bid] = rect
            mouse = pygame.mouse.get_pos()
            fill = (221, 184, 100) if rect.collidepoint(mouse) else (210, 202, 176)
            pygame.draw.rect(self.screen, fill, rect, border_radius=8)
            pygame.draw.rect(self.screen, (85, 73, 49), rect, 1, border_radius=8)

            label = "N" if bid == 0 else str(bid)
            text = self.small_font.render(label, True, (38, 43, 40))
            self.screen.blit(text, text.get_rect(center=rect.center))

    def _draw_trick(self, model):
        center_x = self.width // 2
        center_y = self.height // 2 + 10

        label = self.small_font.render("CURRENT TRICK", True, (207, 224, 215))
        self.screen.blit(label, label.get_rect(center=(center_x, center_y - 125)))

        positions = {
            0: (center_x, center_y + 72),
            1: (center_x - 145, center_y),
            2: (center_x, center_y - 62),
            3: (center_x + 145, center_y),
        }

        for player_index, card in model.current_trick:
            x, y = positions[player_index]
            rect = pygame.Rect(
                x - self.CARD_W // 2,
                y - self.CARD_H // 2,
                self.CARD_W,
                self.CARD_H,
            )
            self.draw_card(card, rect, enabled=True)

    def _draw_human_hand(self, model, hand_revealed):
        self.card_rects = []

        player = model.current_player
        if not player.is_human or not hand_revealed:
            return

        valid = set(model.get_valid_cards())
        self._draw_hand_cards(
            player.hand,
            enabled_cards=valid,
            y=self.height - self.CARD_H - 20,
            clickable=True,
        )

    def _draw_hand_cards(self, cards, enabled_cards, y, clickable=False):
        if not cards:
            return

        max_width = self.width - 90
        spacing = min(
            61,
            max(31, (max_width - self.CARD_W) // max(1, len(cards) - 1)),
        )
        total_width = self.CARD_W + spacing * (len(cards) - 1)
        start_x = (self.width - total_width) // 2
        mouse = pygame.mouse.get_pos()

        for index, card in enumerate(cards):
            rect = pygame.Rect(
                start_x + index * spacing,
                y,
                self.CARD_W,
                self.CARD_H,
            )

            enabled = card in enabled_cards
            if enabled and rect.collidepoint(mouse):
                rect.y -= 11

            self.draw_card(card, rect, enabled=enabled)

            if clickable:
                self.card_rects.append((rect, card))

    def draw_card(self, card, rect, enabled=True):
        shadow = rect.move(4, 5)
        pygame.draw.rect(self.screen, (12, 47, 35), shadow, border_radius=10)

        body = (250, 248, 240) if enabled else (180, 185, 181)
        pygame.draw.rect(self.screen, body, rect, border_radius=10)
        pygame.draw.rect(self.screen, (42, 42, 42), rect, 2, border_radius=10)

        color = (181, 35, 43) if card.is_red else (25, 28, 31)
        if not enabled:
            color = (100, 103, 101)

        rank = self.card_font.render(card.rank, True, color)
        suit_small = self.card_font.render(card.symbol, True, color)
        suit_big = self.suit_font.render(card.symbol, True, color)

        self.screen.blit(rank, (rect.x + 7, rect.y + 4))
        self.screen.blit(suit_small, (rect.x + 7, rect.y + 29))
        self.screen.blit(
            suit_big,
            suit_big.get_rect(center=(rect.centerx, rect.centery + 7)),
        )

    def _draw_privacy_overlay(self, model):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((4, 15, 12, 225))
        self.screen.blit(overlay, (0, 0))

        if model.phase == "bidding":
            player = model.current_bidder
            action = "bid"
        else:
            player = model.current_player
            action = "play"

        title = self.heading_font.render(
            f"Pass the device to {player.name}",
            True,
            (248, 239, 211),
        )
        self.screen.blit(
            title,
            title.get_rect(center=(self.width // 2, self.height // 2 - 55)),
        )

        text = self.font.render(
            f"Other players should look away before {player.name} reveals their hand to {action}.",
            True,
            (205, 220, 212),
        )
        self.screen.blit(
            text,
            text.get_rect(center=(self.width // 2, self.height // 2 - 16)),
        )

        self._draw_button(self.reveal_rect, "Reveal Hand", large=True)

    def needs_privacy_overlay(self, model, hand_revealed):
        if hand_revealed:
            return False

        if model.phase == "bidding":
            return model.current_bidder.is_human

        if model.phase == "playing":
            return model.current_player.is_human

        return False

    def _draw_hand_score(self, model):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 155))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(self.width // 2 - 390, 175, 780, 480)
        pygame.draw.rect(self.screen, (242, 236, 215), panel, border_radius=18)
        pygame.draw.rect(self.screen, (75, 62, 40), panel, 3, border_radius=18)

        heading = self.heading_font.render(
            f"Hand {model.hand_number} Results",
            True,
            (37, 46, 41),
        )
        self.screen.blit(
            heading,
            heading.get_rect(center=(self.width // 2, panel.y + 38)),
        )

        y = panel.y + 78

        for detail in model.hand_score_details:
            made = "Made bid" if detail["made_contract"] else "Set"
            line = (
                f'{detail["team"]}: bid {detail["bid"]}, '
                f'contract tricks {detail["contract_tricks"]}, '
                f'{made}, hand score {detail["delta"]:+d}'
            )
            text = self.font.render(line, True, (43, 51, 47))
            self.screen.blit(text, (panel.x + 32, y))
            y += 29

            bag_text = self.small_font.render(
                f'Bags this hand: {detail["hand_bags"]} • '
                f'Bags carried: {detail["bags_after"]}/10 • '
                f'Total score: {detail["score"]}',
                True,
                (78, 86, 82),
            )
            self.screen.blit(bag_text, (panel.x + 52, y))
            y += 25

            for note in detail["nil_notes"]:
                nil_text = self.small_font.render(note, True, (121, 67, 49))
                self.screen.blit(nil_text, (panel.x + 52, y))
                y += 22

            if detail["bag_penalties"]:
                penalty = self.small_font.render(
                    f'Bag penalty: -{detail["bag_penalties"] * 100}',
                    True,
                    (155, 52, 52),
                )
                self.screen.blit(penalty, (panel.x + 52, y))
                y += 22

            y += 18

        player_y = panel.bottom - 115
        player_summary = "   |   ".join(
            f"{p.name}: bid {'Nil' if p.bid == 0 else p.bid}, won {p.tricks_won}"
            for p in model.players
        )
        small = self.tiny_font.render(player_summary, True, (75, 82, 78))
        self.screen.blit(
            small,
            small.get_rect(center=(self.width // 2, player_y)),
        )

        self._draw_button(self.next_hand_rect, "Deal Next Hand", large=True)

    def _draw_game_over(self, model):
        overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 190))
        self.screen.blit(overlay, (0, 0))

        panel = pygame.Rect(self.width // 2 - 315, self.height // 2 - 175, 630, 350)
        pygame.draw.rect(self.screen, (244, 238, 217), panel, border_radius=20)
        pygame.draw.rect(self.screen, (76, 63, 40), panel, 3, border_radius=20)

        spade = self.title_font.render("♠", True, (34, 41, 38))
        self.screen.blit(spade, spade.get_rect(center=(self.width // 2, panel.y + 52)))

        title = self.heading_font.render("GAME OVER", True, (34, 41, 38))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, panel.y + 92)))

        winner = self.font.render(model.game_winner_text, True, (45, 52, 48))
        self.screen.blit(
            winner,
            winner.get_rect(center=(self.width // 2, panel.y + 137)),
        )

        team1 = model.teams[0]
        team2 = model.teams[1]
        score = self.heading_font.render(
            f"{team1.name} {team1.score}   —   {team2.score} {team2.name}",
            True,
            (63, 69, 66),
        )
        self.screen.blit(
            score,
            score.get_rect(center=(self.width // 2, panel.y + 190)),
        )

        hint = self.small_font.render(
            "Restart starts a new game. Menu changes the player setup.",
            True,
            (84, 91, 87),
        )
        self.screen.blit(
            hint,
            hint.get_rect(center=(self.width // 2, panel.bottom - 45)),
        )

    def _draw_button(self, rect, label, large=False):
        mouse = pygame.mouse.get_pos()
        fill = (239, 205, 130) if rect.collidepoint(mouse) else (222, 192, 123)

        pygame.draw.rect(self.screen, fill, rect, border_radius=10)
        pygame.draw.rect(self.screen, (70, 55, 34), rect, 2, border_radius=10)

        font = self.font if large else self.small_font
        text = font.render(label, True, (35, 40, 37))
        self.screen.blit(text, text.get_rect(center=rect.center))

    def get_clicked_card(self, pos):
        for rect, card in reversed(self.card_rects):
            if rect.collidepoint(pos):
                return card
        return None

    def get_clicked_bid(self, pos):
        for bid, rect in self.bid_rects.items():
            if rect.collidepoint(pos):
                return bid
        return None
