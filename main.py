"""Main entry point for Four of a Kind.

Manages the top-level application loop, display surface, immutable GameState,
and screen transitions between the Chapter Hub, dedicated playable levels (e.g. The Plan),
and generic chapter environments.
"""

import sys
import pygame

from chapter_screen import ChapterScreen
from game_state import CHAPTER_THE_PLAN, GameState, complete_chapter, set_current_chapter
from hub import HubScreen
from level_plan import ThePlanLevel
from settings import FPS, SCREEN_HEIGHT, SCREEN_WIDTH, TITLE


class Game:
    """Coordinates screen transitions, event distribution, updates, and rendering."""

    def __init__(self):
        pygame.init()
        pygame.font.init()

        # Window setup
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)

        # Timing and state
        self.clock = pygame.time.Clock()
        self.is_running = True

        # Central immutable game state
        self.state: GameState = GameState()

        # Modular screens
        self.hub_screen = HubScreen()
        self.chapter_screen = ChapterScreen()
        self.plan_level = ThePlanLevel()

    def handle_events(self):
        """Poll OS and user inputs, dispatching to active screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            if self.state.current_chapter is None:
                # We are at the Hub screen
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.is_running = False
                    return

                selected_chapter = self.hub_screen.handle_event(event, self.state)
                if selected_chapter is not None:
                    # Transition to selected chapter
                    self.state = set_current_chapter(self.state, selected_chapter)
                    if selected_chapter == CHAPTER_THE_PLAN:
                        self.plan_level.reset()
                    else:
                        self.chapter_screen.reset_player_position()

            elif self.state.current_chapter == CHAPTER_THE_PLAN:
                # Playable level for Chapter 1: The Plan
                action, new_state = self.plan_level.handle_event(event, self.state)
                self.state = new_state
                if action == "return_to_hub":
                    self.state = set_current_chapter(self.state, None)

            else:
                # Generic fallback for other active chapters
                action = self.chapter_screen.handle_event(event, self.state)
                if action == "return_to_hub":
                    self.state = set_current_chapter(self.state, None)
                elif action == "complete":
                    self.state = complete_chapter(self.state, self.state.current_chapter)

    def update(self, dt: float):
        """Update active screen simulation."""
        if self.state.current_chapter == CHAPTER_THE_PLAN:
            self.plan_level.update(dt)
        elif self.state.current_chapter is not None:
            self.chapter_screen.update(dt)

    def draw(self):
        """Render active screen to the display."""
        if self.state.current_chapter is None:
            self.hub_screen.draw(self.screen, self.state)
        elif self.state.current_chapter == CHAPTER_THE_PLAN:
            self.plan_level.draw(self.screen, self.state)
        else:
            self.chapter_screen.draw(self.screen, self.state)

        pygame.display.flip()

    def run(self):
        """Main game loop."""
        while self.is_running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            self.update(dt)
            self.draw()

        self.cleanup()

    def cleanup(self):
        """Cleanly terminate Pygame and system process."""
        pygame.quit()
        sys.exit()


def main():
    game = Game()
    game.run()


if __name__ == "__main__":
    main()
