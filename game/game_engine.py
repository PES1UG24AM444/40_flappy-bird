import pygame
from pathlib import Path
from .bird import Bird
from .pipe import Pipe

# Game Engine

WHITE = (255, 255, 255)
GREEN = (0, 150, 0)
DARK_GREEN = (0, 110, 0)
DIFFICULTIES = {
    "easy": {"speed": 3, "gap": 190},
    "medium": {"speed": 4, "gap": 150},
    "hard": {"speed": 6, "gap": 120},
}

class GameEngine:
    def __init__(self, width, height, project_root=None):
        self.width = width
        self.height = height
        self.sounds = self._load_sounds(project_root)

        self.pipe_interval = 90  # frames between pipe spawns
        self.font = pygame.font.SysFont("Arial", 30)
        self.game_over_font = pygame.font.SysFont("Arial", 48, bold=True)
        self.final_score_font = pygame.font.SysFont("Arial", 36, bold=True)
        self.instruction_font = pygame.font.SysFont("Arial", 22)
        self.menu_font = pygame.font.SysFont("Arial", 26, bold=True)
        self.menu_options = ["Easy", "Medium", "Hard", "Exit"]
        self.menu_buttons = self._make_menu_buttons()

        self.difficulty = "medium"
        self.pipe_speed = DIFFICULTIES[self.difficulty]["speed"]
        self.pipe_gap = DIFFICULTIES[self.difficulty]["gap"]
        self.bird = Bird(width // 4, height // 2)
        self._spawn_timer = 0
        self.pipes = [Pipe(width + 100, height, gap=self.pipe_gap, speed=self.pipe_speed)]

        self.score = 0
        self.game_over = False

    def _load_sounds(self, project_root):
        if not pygame.mixer.get_init():
            return {}

        sound_dir = Path(project_root or Path(__file__).parent.parent) / "game" / "assets" / "sounds"
        sounds = {}
        for name in ("flap", "score", "death"):
            try:
                sounds[name] = pygame.mixer.Sound(str(sound_dir / f"{name}.wav"))
            except (pygame.error, OSError):
                sounds[name] = None
        return sounds

    def _play_sound(self, name):
        sound = self.sounds.get(name)
        if sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def _set_game_over(self):
        if not self.game_over:
            self.game_over = True
            self._play_sound("death")

    def _make_menu_buttons(self):
        button_width = min(300, self.width - 40)
        button_height = 48
        gap = 12
        first_y = self.height // 2 - 35
        return [
            pygame.Rect((self.width - button_width) // 2,
                        first_y + index * (button_height + gap),
                        button_width, button_height)
            for index in range(len(self.menu_options))
        ]

    def reset(self, difficulty):
        settings = DIFFICULTIES[difficulty]
        self.difficulty = difficulty
        self.pipe_speed = settings["speed"]
        self.pipe_gap = settings["gap"]
        self.bird = Bird(self.width // 4, self.height // 2)
        self.pipes = [Pipe(self.width + 100, self.height,
                           gap=self.pipe_gap, speed=self.pipe_speed)]
        self.score = 0
        self.game_over = False
        self._spawn_timer = 0

    def handle_event(self, event):
        if self.game_over:
            if event.type == pygame.KEYDOWN:
                choices = {
                    pygame.K_1: "easy",
                    pygame.K_2: "medium",
                    pygame.K_3: "hard",
                }
                if event.key in choices:
                    return choices[event.key]
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    return "exit"
            elif event.type == pygame.MOUSEBUTTONDOWN:
                for option, button in zip(self.menu_options, self.menu_buttons):
                    if button.collidepoint(event.pos):
                        return option.lower()
            return None

        # Flap is edge-triggered (KEYDOWN / MOUSEBUTTONDOWN), not held.
        if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
            self.bird.flap()
            self._play_sound("flap")
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.bird.flap()
            self._play_sound("flap")

    def handle_input(self):
        # Reserved for continuously-held-key input; flapping is handled
        # in handle_event instead, so there's nothing to poll here.
        pass

    def update(self):
        if self.game_over:
            return

        self.bird.update()

        if self.bird.y - self.bird.radius <= 0 or self.bird.y + self.bird.radius >= self.height:
            self._set_game_over()
            return

        self._spawn_timer += 1
        if self._spawn_timer >= self.pipe_interval:
            self._spawn_timer = 0
            self.pipes.append(Pipe(self.width, self.height, gap=self.pipe_gap, speed=self.pipe_speed))

        for pipe in self.pipes:
            previous_pipe_x = pipe.x
            pipe.move()

            bird_rect = self.bird.rect()
            swept_pipe_x = min(previous_pipe_x, pipe.x)
            swept_pipe_width = pipe.width + abs(previous_pipe_x - pipe.x)
            if (pygame.Rect(swept_pipe_x, 0, swept_pipe_width, pipe.gap_y).colliderect(bird_rect)
                    or pygame.Rect(swept_pipe_x, pipe.gap_y + pipe.gap, swept_pipe_width,
                                   pipe.screen_height - pipe.gap_y - pipe.gap).colliderect(bird_rect)):
                self._set_game_over()

            if not pipe.scored and pipe.x + pipe.width < self.bird.x:
                pipe.scored = True
                self.score += 1
                self._play_sound("score")

        self.pipes = [p for p in self.pipes if not p.off_screen()]

    def render(self, screen):
        for pipe in self.pipes:
            pygame.draw.rect(screen, GREEN, pipe.top_rect())
            pygame.draw.rect(screen, GREEN, pipe.bottom_rect())

        pygame.draw.circle(screen, WHITE, (int(self.bird.x), int(self.bird.y)), self.bird.radius)

        score_text = self.font.render(f"Score: {self.score}", True, WHITE)
        screen.blit(score_text, (10, 10))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))

            title = self.game_over_font.render("Game Over", True, WHITE)
            final_score = self.final_score_font.render(f"Final Score: {self.score}", True, WHITE)
            screen.blit(title, title.get_rect(center=(self.width // 2, self.height // 2 - 185)))
            screen.blit(final_score, final_score.get_rect(center=(self.width // 2, self.height // 2 - 135)))
            instruction = self.instruction_font.render("Choose a difficulty or exit", True, WHITE)
            screen.blit(instruction, instruction.get_rect(center=(self.width // 2, self.height // 2 - 90)))

            for option, button in zip(self.menu_options, self.menu_buttons):
                pygame.draw.rect(screen, DARK_GREEN, button, border_radius=8)
                label = self.menu_font.render(option, True, WHITE)
                screen.blit(label, label.get_rect(center=button.center))
