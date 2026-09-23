from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


import pygame

from controller.MenuController import MenuController
from controller.GameController import GameController
from model.GameModel import GameModel
from view.MenuView import MenuView
from view.GameView import GameView


WIDTH = 1280
HEIGHT = 800
FPS = 60


def main():
    pygame.init()

    try:
        pygame.mixer.init()
    except pygame.error:
        pass

    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Spades MVC")

    clock = pygame.time.Clock()

    menu_view = MenuView(screen)
    menu_controller = MenuController(menu_view)

    game_model = None
    game_view = None
    game_controller = None

    state = "menu"
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                continue

            if state == "menu":
                action = menu_controller.handle_event(event)

                if action == "quit":
                    running = False
                elif isinstance(action, int):
                    game_model = GameModel(human_count=action)
                    game_view = GameView(screen)
                    game_controller = GameController(game_model, game_view)
                    state = "game"

            elif state == "game":
                action = game_controller.handle_event(event)

                if action == "menu":
                    state = "menu"

        if state == "menu":
            menu_view.draw()
        else:
            game_controller.update()
            game_controller.draw()

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()
