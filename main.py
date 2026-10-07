import pygame
from game.game_engine import GameEngine
from pathlib import Path

# Initialize pygame audio before the display and game engine.
pygame.mixer.pre_init(frequency=22050, size=-16, channels=1, buffer=512)
pygame.init()
if not pygame.mixer.get_init():
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=1, buffer=512)
    except pygame.error:
        pass

# Screen dimensions
WIDTH, HEIGHT = 500, 700
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Flappy Bird - Pygame Version")

# Colors
SKY_BLUE = (135, 206, 235)
WHITE = (255, 255, 255)

# Clock
clock = pygame.time.Clock()
FPS = 60

# Game loop
engine = GameEngine(WIDTH, HEIGHT, Path(__file__).parent)

def main():
    running = True
    while running:
        SCREEN.fill(SKY_BLUE)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                action = engine.handle_event(event)
                if action == "exit":
                    running = False
                elif action in ("easy", "medium", "hard"):
                    engine.reset(action)

        engine.handle_input()
        engine.update()
        engine.render(SCREEN)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
