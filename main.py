"""Main entry point for Four of a Kind.

Manages the top-level application loop, display surface, immutable GameState,
screen transitions between the Chapter Hub, dedicated playable levels (e.g. The Plan),
generic chapter environments, and an on-screen debug overlay showing current flags.
"""

import sys
import pygame

from chapter_screen import ChapterScreen
from game_state import CHAPTER_THE_PLAN, GameState, complete_chapter, set_current_chapter
from hub import HubScreen
from level_plan import ThePlanLevel
from settings import (
    COLOR_CARD_BORDER,
    COLOR_COMPLETED,
    COLOR_MUTED,
    COLOR_TEXT,
    FPS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    TITLE,
)


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

        # On-screen debug flags overlay (enabled by default; toggle with F3 or ~)
        self.show_debug: bool = True
        self.debug_font = pygame.font.SysFont("Consolas, monospace, Segoe UI", 12)
        self.debug_hint_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 10)

    def handle_events(self):
        """Poll OS and user inputs, dispatching to active screen."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.is_running = False
                return

            # Toggle debug overlay with F3 or Tilde (`)
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_F3, pygame.K_BACKQUOTE):
                self.show_debug = not self.show_debug
                continue

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

    def _draw_debug_overlay(self):
        """Render temporary on-screen debug box displaying current flags and state."""
        flags_list = sorted(list(self.state.flags))
        flags_text = ", ".join(flags_list) if flags_list else "(none)"

        box_w = 270
        box_h = 58
        box_x = SCREEN_WIDTH - box_w - 15
        box_y = 12
        box_rect = pygame.Rect(box_x, box_y, box_w, box_h)

        # Semi-transparent dark background
        bg_surface = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        bg_surface.fill((16, 22, 32, 230))
        self.screen.blit(bg_surface, (box_x, box_y))

        # Border
        border_col = (70, 140, 240) if flags_list else COLOR_CARD_BORDER
        pygame.draw.rect(self.screen, border_col, box_rect, width=1, border_radius=6)

        # Header Title
        count_tag = f"[{len(flags_list)}]"
        header_surf = self.debug_font.render(f"[DEBUG] FLAGS {count_tag}", True, (100, 180, 255))
        self.screen.blit(header_surf, (box_x + 10, box_y + 8))

        # Hint toggle
        hint_surf = self.debug_hint_font.render("[F3] Hide", True, COLOR_MUTED)
        self.screen.blit(hint_surf, (box_x + box_w - hint_surf.get_width() - 10, box_y + 9))

        # Flags content
        val_color = COLOR_COMPLETED if flags_list else COLOR_MUTED
        val_surf = self.debug_font.render(flags_text, True, val_color)
        self.screen.blit(val_surf, (box_x + 10, box_y + 28))

    def draw(self):
        """Render active screen and debug overlay to the display."""
        if self.state.current_chapter is None:
            self.hub_screen.draw(self.screen, self.state)
        elif self.state.current_chapter == CHAPTER_THE_PLAN:
            self.plan_level.draw(self.screen, self.state)
        else:
            self.chapter_screen.draw(self.screen, self.state)

        # Render on-screen debug flags overlay
        if self.show_debug:
            self._draw_debug_overlay()

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
