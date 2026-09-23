import pygame


class MenuView:
    def __init__(self, screen):
        self.screen = screen
        self.width, self.height = screen.get_size()

        self.title_font = pygame.font.SysFont("georgia", 62, bold=True)
        self.subtitle_font = pygame.font.SysFont("arial", 23)
        self.button_font = pygame.font.SysFont("arial", 24, bold=True)
        self.small_font = pygame.font.SysFont("arial", 17)

        button_width = 430
        button_height = 58
        x = (self.width - button_width) // 2

        self.buttons = {
            1: pygame.Rect(x, 300, button_width, button_height),
            2: pygame.Rect(x, 375, button_width, button_height),
            4: pygame.Rect(x, 450, button_width, button_height),
        }

    def draw(self):
        self.screen.fill((13, 49, 38))

        # Decorative table surface.
        pygame.draw.ellipse(
            self.screen,
            (21, 87, 62),
            pygame.Rect(120, 70, self.width - 240, self.height - 120),
        )
        pygame.draw.ellipse(
            self.screen,
            (161, 120, 62),
            pygame.Rect(120, 70, self.width - 240, self.height - 120),
            6,
        )

        title = self.title_font.render("SPADES", True, (249, 239, 208))
        self.screen.blit(title, title.get_rect(center=(self.width // 2, 125)))

        spade = self.title_font.render("♠", True, (249, 239, 208))
        self.screen.blit(spade, spade.get_rect(center=(self.width // 2, 190)))

        subtitle = self.subtitle_font.render(
            "Partnership Spades • First team to 500",
            True,
            (217, 229, 222),
        )
        self.screen.blit(
            subtitle,
            subtitle.get_rect(center=(self.width // 2, 242)),
        )

        labels = {
            1: "1 Human + 3 Smart Computers",
            2: "2 Humans + 2 Smart Computers",
            4: "4 Local Human Players",
        }

        mouse = pygame.mouse.get_pos()

        for human_count, rect in self.buttons.items():
            hovered = rect.collidepoint(mouse)
            fill = (239, 205, 130) if hovered else (224, 190, 118)

            pygame.draw.rect(self.screen, fill, rect, border_radius=14)
            pygame.draw.rect(self.screen, (66, 52, 31), rect, 2, border_radius=14)

            text = self.button_font.render(labels[human_count], True, (31, 38, 34))
            self.screen.blit(text, text.get_rect(center=rect.center))

        rules = self.small_font.render(
            "Teams sit opposite • Bid tricks • Nil = ±100 • 10 bags = −100 • Spades are trump",
            True,
            (202, 219, 210),
        )
        self.screen.blit(
            rules,
            rules.get_rect(center=(self.width // 2, self.height - 75)),
        )

        quit_text = self.small_font.render(
            "Press ESC to quit",
            True,
            (150, 180, 166),
        )
        self.screen.blit(
            quit_text,
            quit_text.get_rect(center=(self.width // 2, self.height - 42)),
        )
