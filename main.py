"""Main entry point for Four of a Kind.

Manages the top-level application loop, display surface, immutable GameState,
and screen transitions between the Chapter Hub and active chapter environments.
"""

import sys
import pygame

from chapter_screen import ChapterScreen
from game_state import GameState, complete_chapter, set_current_chapter
from hub import HubScreen
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
                    self.chapter_screen.reset_player_position()

            else:
                # We are inside an active chapter
                action = self.chapter_screen.handle_event(event, self.state)
                if action == "return_to_hub":
                    # Transition back to hub screen
                    self.state = set_current_chapter(self.state, None)
                elif action == "complete":
                    # Mark active chapter as completed in state
                    self.state = complete_chapter(self.state, self.state.current_chapter)

    def update(self, dt: float):
        """Update active screen simulation."""
        if self.state.current_chapter is not None:
            self.chapter_screen.update(dt)

    def draw(self):
        """Render active screen to the display."""
        if self.state.current_chapter is None:
            self.hub_screen.draw(self.screen, self.state)
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
