"""Hub screen module for chapter selection.

Renders the chapter hub, handles keyboard and mouse navigation, and transitions
into selected chapters. Dynamically displays the 'Finale' option only when all
7 core chapters are marked as completed.
"""

from typing import List, Optional, Tuple
import pygame

from game_state import (
    CHAPTERS,
    FINALE_CHAPTER,
    GameState,
    get_available_chapters,
    is_finale_unlocked,
)
from settings import (
    COLOR_AVAILABLE,
    COLOR_BACKGROUND,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CARD_HOVER,
    COLOR_COMPLETED,
    COLOR_COMPLETED_BG,
    COLOR_FINALE,
    COLOR_FINALE_BG,
    COLOR_FINALE_BORDER,
    COLOR_FINALE_HOVER,
    COLOR_MUTED,
    COLOR_SELECTED,
    COLOR_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


class HubScreen:
    """Manages the Chapter Hub menu presentation, navigation, and selection."""

    def __init__(self):
        # Selected index in the available chapters list
        self.selected_index: int = 0

        # Cached item bounding rectangles for mouse collision detection
        self.item_rects: List[Tuple[str, pygame.Rect]] = []

        # UI fonts
        self.title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 32, bold=True)
        self.subtitle_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 16)
        self.item_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)
        self.badge_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.footer_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 14)

    def handle_event(self, event: pygame.event.Event, state: GameState) -> Optional[str]:
        """Process input events and return selected chapter name if activated."""
        available = get_available_chapters(state)
        total = len(available)
        if total == 0:
            return None

        # Clamp selection index within bounds if list changed
        self.selected_index = max(0, min(self.selected_index, total - 1))

        if event.type == pygame.KEYDOWN:
            # Navigate Up
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected_index = (self.selected_index - 1) % total
                return None

            # Navigate Down
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected_index = (self.selected_index + 1) % total
                return None

            # Confirm Selection
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return available[self.selected_index]

            # Number key shortcuts (1-7 for chapters, 8 for Finale if available)
            elif pygame.K_1 <= event.key <= pygame.K_9:
                key_index = event.key - pygame.K_1
                if 0 <= key_index < total:
                    self.selected_index = key_index
                    return available[key_index]

        elif event.type == pygame.MOUSEMOTION:
            mouse_pos = event.pos
            for idx, (_, rect) in enumerate(self.item_rects):
                if rect.collidepoint(mouse_pos):
                    self.selected_index = idx
                    break

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                mouse_pos = event.pos
                for idx, (chapter_name, rect) in enumerate(self.item_rects):
                    if rect.collidepoint(mouse_pos):
                        self.selected_index = idx
                        return chapter_name

        return None

    def draw(self, surface: pygame.Surface, state: GameState):
        """Render the chapter selection hub onto the given surface."""
        surface.fill(COLOR_BACKGROUND)

        available = get_available_chapters(state)
        total_items = len(available)
        finale_unlocked = is_finale_unlocked(state)

        # -------------------------------------------------------------------
        # 1. Header (Title & Subtitle)
        # -------------------------------------------------------------------
        title_surf = self.title_font.render("FOUR OF A KIND", True, COLOR_TEXT)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 40))
        surface.blit(title_surf, title_rect)

        # Subtitle and progress counter
        completed_count = len(state.completed_chapters & set(CHAPTERS))
        if finale_unlocked:
            sub_text = "★ ALL 7 CHAPTERS COMPLETE — FINALE UNLOCKED ★"
            sub_color = COLOR_FINALE
        else:
            sub_text = f"CHAPTER SELECT   |   COMPLETED: {completed_count} / {len(CHAPTERS)}"
            sub_color = COLOR_MUTED

        sub_surf = self.subtitle_font.render(sub_text, True, sub_color)
        sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 75))
        surface.blit(sub_surf, sub_rect)

        # Subtle divider line
        pygame.draw.line(surface, COLOR_CARD_BORDER, (120, 96), (SCREEN_WIDTH - 120, 96), 1)

        # -------------------------------------------------------------------
        # 2. Chapter Cards List
        # -------------------------------------------------------------------
        card_width = 540
        card_height = 42
        card_gap = 10
        start_y = 112

        self.item_rects.clear()

        for idx, chapter_name in enumerate(available):
            card_y = start_y + idx * (card_height + card_gap)
            card_x = (SCREEN_WIDTH - card_width) // 2
            card_rect = pygame.Rect(card_x, card_y, card_width, card_height)
            self.item_rects.append((chapter_name, card_rect))

            is_selected = idx == self.selected_index
            is_completed = chapter_name in state.completed_chapters
            is_finale = chapter_name == FINALE_CHAPTER

            # Determine background and border colors
            if is_finale:
                bg_color = COLOR_FINALE_HOVER if is_selected else COLOR_FINALE_BG
                border_color = COLOR_FINALE if is_selected else COLOR_FINALE_BORDER
                border_width = 2 if is_selected else 1
            else:
                bg_color = COLOR_CARD_HOVER if is_selected else COLOR_CARD_BG
                border_color = COLOR_SELECTED if is_selected else COLOR_CARD_BORDER
                border_width = 2 if is_selected else 1

            # Draw card body and outline
            pygame.draw.rect(surface, bg_color, card_rect, border_radius=6)
            pygame.draw.rect(surface, border_color, card_rect, width=border_width, border_radius=6)

            # Left selection indicator accent pill
            if is_selected:
                pill_color = COLOR_FINALE if is_finale else COLOR_SELECTED
                accent_rect = pygame.Rect(card_x + 3, card_y + 6, 4, card_height - 12)
                pygame.draw.rect(surface, pill_color, accent_rect, border_radius=2)

            # Chapter Title Text
            if is_finale:
                label_text = f"★  {chapter_name.upper()}  ★"
                label_color = COLOR_FINALE
            else:
                label_text = f"{idx + 1}.  {chapter_name}"
                label_color = COLOR_TEXT if not is_completed else (210, 220, 230)

            label_surf = self.item_font.render(label_text, True, label_color)
            label_rect = label_surf.get_rect(midleft=(card_x + 20, card_rect.centery))
            surface.blit(label_surf, label_rect)

            # Right Status Badge
            if is_completed:
                badge_text = " COMPLETED ✓ "
                badge_fg = COLOR_COMPLETED
                badge_bg = COLOR_COMPLETED_BG
            elif is_finale:
                badge_text = " UNLOCKED "
                badge_fg = COLOR_FINALE
                badge_bg = COLOR_FINALE_BG
            else:
                badge_text = " AVAILABLE "
                badge_fg = COLOR_AVAILABLE
                badge_bg = COLOR_CARD_BG

            badge_surf = self.badge_font.render(badge_text, True, badge_fg)
            badge_rect = badge_surf.get_rect(midright=(card_x + card_width - 15, card_rect.centery))

            # Badge pill background
            bg_pad = 4
            pill_rect = badge_rect.inflate(bg_pad * 2, bg_pad)
            pygame.draw.rect(surface, badge_bg, pill_rect, border_radius=4)
            pygame.draw.rect(surface, badge_fg, pill_rect, width=1, border_radius=4)
            surface.blit(badge_surf, badge_rect)

        # -------------------------------------------------------------------
        # 3. Footer Navigation Hints
        # -------------------------------------------------------------------
        footer_text = "▲/▼ or W/S: Navigate   |   ENTER / Click: Select Chapter   |   ESC: Quit"
        footer_surf = self.footer_font.render(footer_text, True, COLOR_MUTED)
        footer_rect = footer_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 25))
        surface.blit(footer_surf, footer_rect)
