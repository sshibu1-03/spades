import pygame


class MenuController:
    def __init__(self, view):
        self.view = view

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "quit"

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for human_count, rect in self.view.buttons.items():
                if rect.collidepoint(event.pos):
                    return human_count

        return None
