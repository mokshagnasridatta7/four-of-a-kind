"""Chapter screen module.

Renders the active chapter environment, manages the playable character sprite,
displays chapter narrative details, and allows the player to mark the chapter complete
or return to the Hub.
"""

from typing import Dict, Optional
import pygame

from game_state import FINALE_CHAPTER, GameState
from player import Player
from settings import (
    COLOR_BACKGROUND,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_COMPLETED,
    COLOR_COMPLETED_BG,
    COLOR_FINALE,
    COLOR_MUTED,
    COLOR_SELECTED,
    COLOR_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

# Brief narrative contexts for each chapter
CHAPTER_BRIEFINGS: Dict[str, str] = {
    "The Plan": "Safehouse hideout. Review the target vault schematics and finalize crew assignments.",
    "The Watcher": "High-rise rooftop surveillance. Monitor security patrol rotations and blind spots.",
    "The Signal": "Secure underground radio comms. Await the green light from Sana before breaching.",
    "The Job": "Target deposit room infiltration. Bypass biometric lasers and crack the lockbox.",
    "The Getaway": "Downtown high-speed pursuit. Evade law enforcement cruisers through back alleys.",
    "The Split": "Abandoned shipyard dock. Distribute the diamonds, but Kabir's ledger doesn't add up.",
    "The Fallout": "Safehouse aftermath. Analyze tapped phone calls and uncover the traitor's tracks.",
    "Finale": "The confrontation. All cards on the table. Face the betrayal and determine the crew's fate.",
}


class ChapterScreen:
    """Manages the interactive scene of an active chapter."""

    def __init__(self):
        # Interactive player sprite for the chapter room
        self.all_sprites = pygame.sprite.Group()
        self.player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
        self.all_sprites.add(self.player)

        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 28, bold=True)
        self.desc_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 15)
        self.btn_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 15, bold=True)
        self.badge_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.hud_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 14)

        # Button rects for mouse interaction
        self.btn_hub_rect = pygame.Rect(30, 20, 150, 36)
        self.btn_complete_rect = pygame.Rect(SCREEN_WIDTH - 230, 20, 200, 36)

    def reset_player_position(self):
        """Reset player to the chapter starting position."""
        self.player.rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 50)
        self.player.pos = pygame.math.Vector2(self.player.rect.center)

    def handle_event(self, event: pygame.event.Event, state: GameState) -> Optional[str]:
        """Handle chapter inputs.

        Returns:
            'return_to_hub' if player exits back to hub.
            'complete' if player marks the chapter complete.
            None otherwise.
        """
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_h):
                return "return_to_hub"
            elif event.key == pygame.K_c:
                return "complete"

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_hub_rect.collidepoint(event.pos):
                return "return_to_hub"
            elif self.btn_complete_rect.collidepoint(event.pos):
                return "complete"

        return None

    def update(self, dt: float):
        """Update sprites in the chapter environment."""
        self.all_sprites.update(dt)

    def draw(self, surface: pygame.Surface, state: GameState):
        """Draw the chapter environment, player sprite, and UI controls."""
        chapter_name = state.current_chapter or "Unknown"
        is_completed = chapter_name in state.completed_chapters
        is_finale = chapter_name == FINALE_CHAPTER

        # Clear background with subtle grid
        surface.fill(COLOR_BACKGROUND)
        self._draw_room_grid(surface)

        # Draw player sprite
        self.all_sprites.draw(surface)

        # Top Bar & Navigation Buttons
        self._draw_buttons(surface, is_completed)

        # Chapter Information Card
        self._draw_briefing_card(surface, chapter_name, is_completed, is_finale)

        # Bottom HUD Controls Guide
        self._draw_footer(surface)

    def _draw_room_grid(self, surface: pygame.Surface):
        """Render a subtle ambient grid on the room floor."""
        grid_color = (26, 32, 44)
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(surface, grid_color, (x, 180), (x, SCREEN_HEIGHT - 60))
        for y in range(180, SCREEN_HEIGHT - 60, 40):
            pygame.draw.line(surface, grid_color, (0, y), (SCREEN_WIDTH, y))

    def _draw_buttons(self, surface: pygame.Surface, is_completed: bool):
        """Render interactive top navigation buttons."""
        mouse_pos = pygame.mouse.get_pos()

        # 'Return to Hub' button
        hub_hover = self.btn_hub_rect.collidepoint(mouse_pos)
        hub_bg = COLOR_CARD_HOVER if hub_hover else COLOR_CARD_BG
        pygame.draw.rect(surface, hub_bg, self.btn_hub_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.btn_hub_rect, width=1, border_radius=6)
        hub_text = self.btn_font.render("◄ [H] Return to Hub", True, COLOR_TEXT)
        surface.blit(hub_text, hub_text.get_rect(center=self.btn_hub_rect.center))

        # 'Complete Chapter' button
        comp_hover = self.btn_complete_rect.collidepoint(mouse_pos)
        if is_completed:
            comp_bg = COLOR_COMPLETED_BG
            comp_border = COLOR_COMPLETED
            comp_label = "✓ Completed ([C] again)"
            comp_color = COLOR_COMPLETED
        else:
            comp_bg = COLOR_CARD_HOVER if comp_hover else (35, 60, 45)
            comp_border = COLOR_COMPLETED
            comp_label = "[C] Mark Complete"
            comp_color = COLOR_TEXT

        pygame.draw.rect(surface, comp_bg, self.btn_complete_rect, border_radius=6)
        pygame.draw.rect(surface, comp_border, self.btn_complete_rect, width=1, border_radius=6)
        comp_text = self.btn_font.render(comp_label, True, comp_color)
        surface.blit(comp_text, comp_text.get_rect(center=self.btn_complete_rect.center))

    def _draw_briefing_card(
        self, surface: pygame.Surface, chapter_name: str, is_completed: bool, is_finale: bool
    ):
        """Draw chapter briefing banner at the top of the screen."""
        card_rect = pygame.Rect(30, 70, SCREEN_WIDTH - 60, 95)
        accent_color = COLOR_FINALE if is_finale else COLOR_SELECTED

        pygame.draw.rect(surface, COLOR_CARD_BG, card_rect, border_radius=8)
        pygame.draw.rect(surface, accent_color, card_rect, width=2, border_radius=8)

        # Title
        prefix = "★ FINALE: " if is_finale else "CHAPTER: "
        title_surf = self.title_font.render(f"{prefix}{chapter_name.upper()}", True, accent_color)
        surface.blit(title_surf, (card_rect.x + 20, card_rect.y + 14))

        # Status badge next to title
        badge_text = " COMPLETED ✓ " if is_completed else " IN PROGRESS "
        badge_fg = COLOR_COMPLETED if is_completed else COLOR_SELECTED
        badge_surf = self.badge_font.render(badge_text, True, badge_fg)
        badge_rect = badge_surf.get_rect(
            midleft=(card_rect.x + 25 + title_surf.get_width(), card_rect.y + 14 + title_surf.get_height() // 2)
        )
        pill = badge_rect.inflate(8, 4)
        pygame.draw.rect(surface, COLOR_BACKGROUND, pill, border_radius=4)
        pygame.draw.rect(surface, badge_fg, pill, width=1, border_radius=4)
        surface.blit(badge_surf, badge_rect)

        # Narrative Briefing
        briefing = CHAPTER_BRIEFINGS.get(chapter_name, "Investigate the area and take action.")
        desc_surf = self.desc_font.render(briefing, True, COLOR_TEXT)
        surface.blit(desc_surf, (card_rect.x + 20, card_rect.y + 58))

    def _draw_footer(self, surface: pygame.Surface):
        """Render controls and guidance footer."""
        footer_text = "Move: WASD / Arrow Keys   |   [C]: Complete Chapter   |   [H] or ESC: Hub Screen"
        footer_surf = self.hud_font.render(footer_text, True, COLOR_MUTED)
        footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25))
        surface.blit(footer_surf, footer_rect)
