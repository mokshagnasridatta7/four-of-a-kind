"""The Plan - Playable heist planning level.

Provides an interactive safehouse environment where the player:
1. Explores the room using the player sprite.
2. Selects a combination of 3 short-list options: Route, Timing, and Tool.
3. Discovers a hidden interactive detail (Sana's discarded comms radio) that sets
   the flag 'knows_sana_contact' via GameState functions.
4. Executes the formulated plan to call complete_chapter(state, 'The Plan') and
   return to the Hub screen, regardless of whether the secret flag was found.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple
import math
import pygame

from game_state import (
    CHAPTER_THE_PLAN,
    FLAG_KNOWS_SANA_CONTACT,
    GameState,
    complete_chapter,
    has_flag,
    set_current_chapter,
    set_flag,
)
from player import Player
from settings import (
    COLOR_AVAILABLE,
    COLOR_BACKGROUND,
    COLOR_CARD_BG,
    COLOR_CARD_BORDER,
    COLOR_CARD_HOVER,
    COLOR_COMPLETED,
    COLOR_COMPLETED_BG,
    COLOR_FINALE,
    COLOR_MUTED,
    COLOR_SELECTED,
    COLOR_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)

# Puzzle Choice Options (3 choices for each category)
ROUTE_CHOICES: List[Tuple[str, str]] = [
    (
        "Rooftop Ventilation Shaft",
        "Rappel down the central atrium. Bypasses ground sensors but requires zip-lines.",
    ),
    (
        "Underground Service Tunnel",
        "Sub-level drainage line directly beneath vault floor. Damp, dark, and silent.",
    ),
    (
        "Disguised Delivery Dock",
        "Basement intake bay posing as scheduled delivery crew. High foot traffic.",
    ),
]

TIMING_CHOICES: List[Tuple[str, str]] = [
    (
        "02:15 AM — Patrol Shift Rotation",
        "12-minute window during guard changeover. Exterior perimeter watch is halved.",
    ),
    (
        "03:30 AM — System Diagnostic Reboot",
        "Automated backup diagnostics disable biometric cameras for 45 seconds.",
    ),
    (
        "04:45 AM — Pre-dawn Delivery Window",
        "Heavy cargo trucks create acoustic cover and loading bay gates stay unsealed.",
    ),
]

TOOL_CHOICES: List[Tuple[str, str]] = [
    (
        "Thermal Lance",
        "High-temperature burning bar that melts reinforced vault hinges in 30 seconds.",
    ),
    (
        "EMP Disruptor",
        "Electromagnetic pulse device that temporarily blinds laser tripwires and alarms.",
    ),
    (
        "Biometric Keycloner",
        "Sub-dermal frequency cloner spoofing the bank director's palm and retina pass.",
    ),
]


@dataclass
class SafehouseStation:
    """An interactive physical station located in the safehouse room."""

    category: str  # 'route', 'timing', or 'tool'
    name: str
    label: str
    rect: pygame.Rect
    accent_color: Tuple[int, int, int]


class ThePlanLevel:
    """Playable level for Chapter 1: The Plan."""

    def __init__(self):
        # Interactive player sprite
        self.all_sprites = pygame.sprite.Group()
        self.player = Player(SCREEN_WIDTH // 2, 420)
        self.all_sprites.add(self.player)

        # Plan puzzle selections (indices 0, 1, 2 or None)
        self.selected_route_idx: Optional[int] = None
        self.selected_timing_idx: Optional[int] = None
        self.selected_tool_idx: Optional[int] = None

        # Hidden secret status
        self.secret_rect = pygame.Rect(75, 470, 48, 48)
        self.secret_investigated = False
        self.secret_dialog_open = False
        self.secret_toast_timer = 0.0

        # Physical Stations in the safehouse
        self.stations: List[SafehouseStation] = [
            SafehouseStation(
                category="route",
                name="Blueprint Map Table",
                label="[1] Infiltration Route",
                rect=pygame.Rect(80, 240, 130, 80),
                accent_color=(50, 140, 240),
            ),
            SafehouseStation(
                category="timing",
                name="Schedule Terminal",
                label="[2] Security Timing",
                rect=pygame.Rect(335, 240, 130, 80),
                accent_color=(235, 160, 40),
            ),
            SafehouseStation(
                category="tool",
                name="Gear Workbench",
                label="[3] Vault Equipment",
                rect=pygame.Rect(590, 240, 130, 80),
                accent_color=(64, 200, 120),
            ),
        ]

        # Active UI Modal ('route', 'timing', 'tool', 'summary', or None)
        self.active_modal: Optional[str] = None
        self.modal_selection_idx: int = 0
        self.plan_executed_dialog = False

        # UI Navigation Rects
        self.btn_hub_rect = pygame.Rect(25, 18, 140, 34)
        self.btn_execute_rect = pygame.Rect(SCREEN_WIDTH // 2 - 110, 160, 220, 36)

        # Board category slot rects
        self.board_slot_rects: Dict[str, pygame.Rect] = {
            "route": pygame.Rect(40, 75, 220, 72),
            "timing": pygame.Rect(290, 75, 220, 72),
            "tool": pygame.Rect(540, 75, 220, 72),
        }

        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 20, bold=True)
        self.board_title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.board_val_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)
        self.station_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.modal_title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)
        self.modal_opt_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 15, bold=True)
        self.modal_desc_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 12)
        self.prompt_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.footer_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)

        # Pulse timer for ambient animations
        self.ambient_time = 0.0

    def reset(self):
        """Reset player position and puzzle selections."""
        self.player.rect.center = (SCREEN_WIDTH // 2, 420)
        self.player.pos = pygame.math.Vector2(self.player.rect.center)
        self.active_modal = None
        self.secret_dialog_open = False
        self.plan_executed_dialog = False

    def is_plan_complete(self) -> bool:
        """Return True if all three puzzle choices (Route, Timing, Tool) are selected."""
        return (
            self.selected_route_idx is not None
            and self.selected_timing_idx is not None
            and self.selected_tool_idx is not None
        )

    def select_option(self, category: str, option_idx: int):
        """Programmatically select a puzzle option."""
        if category == "route":
            self.selected_route_idx = max(0, min(option_idx, len(ROUTE_CHOICES) - 1))
        elif category == "timing":
            self.selected_timing_idx = max(0, min(option_idx, len(TIMING_CHOICES) - 1))
        elif category == "tool":
            self.selected_tool_idx = max(0, min(option_idx, len(TOOL_CHOICES) - 1))

    def investigate_secret(self, state: GameState) -> GameState:
        """Investigate the hidden detail and set FLAG_KNOWS_SANA_CONTACT."""
        self.secret_investigated = True
        self.secret_dialog_open = True
        self.secret_toast_timer = 4.0
        return set_flag(state, FLAG_KNOWS_SANA_CONTACT)

    def execute_plan(self, state: GameState) -> Tuple[str, GameState]:
        """Finalize the heist plan, complete the chapter, and transition to Hub."""
        new_state = complete_chapter(state, CHAPTER_THE_PLAN)
        new_state = set_current_chapter(new_state, None)
        return "return_to_hub", new_state

    def _get_nearby_station(self) -> Optional[SafehouseStation]:
        """Check if player is near any interactive physical station."""
        player_center = self.player.rect.center
        for station in self.stations:
            dist = math.hypot(
                player_center[0] - station.rect.centerx,
                player_center[1] - station.rect.centery,
            )
            if dist < 85:
                return station
        return None

    def _is_near_secret(self) -> bool:
        """Check if player is near the hidden radio detail."""
        player_center = self.player.rect.center
        dist = math.hypot(
            player_center[0] - self.secret_rect.centerx,
            player_center[1] - self.secret_rect.centery,
        )
        return dist < 65

    def handle_event(
        self, event: pygame.event.Event, state: GameState
    ) -> Tuple[Optional[str], GameState]:
        """Process keyboard, mouse, and interaction events.

        Returns:
            ('return_to_hub', new_state) when exiting or completing.
            (None, state) when continuing inside the level.
        """
        # 1. Secret Dialog Open
        if self.secret_dialog_open:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e, pygame.K_ESCAPE):
                    self.secret_dialog_open = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                self.secret_dialog_open = False
            return None, state

        # 2. Plan Executed Dialog Open (Confirmation popup)
        if self.plan_executed_dialog:
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                    return self.execute_plan(state)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self.execute_plan(state)
            return None, state

        # 3. Active Choice Modal Open
        if self.active_modal in ("route", "timing", "tool"):
            choices_list = (
                ROUTE_CHOICES
                if self.active_modal == "route"
                else (TIMING_CHOICES if self.active_modal == "timing" else TOOL_CHOICES)
            )
            total = len(choices_list)

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.active_modal = None
                elif event.key in (pygame.K_UP, pygame.K_w):
                    self.modal_selection_idx = (self.modal_selection_idx - 1) % total
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.modal_selection_idx = (self.modal_selection_idx + 1) % total
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_e):
                    self.select_option(self.active_modal, self.modal_selection_idx)
                    self.active_modal = None
                elif pygame.K_1 <= event.key <= pygame.K_3:
                    idx = event.key - pygame.K_1
                    if idx < total:
                        self.select_option(self.active_modal, idx)
                        self.active_modal = None

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                # Check modal option cards
                modal_y = 190
                for idx in range(total):
                    opt_rect = pygame.Rect(SCREEN_WIDTH // 2 - 250, modal_y + idx * 72, 500, 62)
                    if opt_rect.collidepoint(mouse_pos):
                        self.select_option(self.active_modal, idx)
                        self.active_modal = None
                        break
                # Click outside modal closes it
                modal_box = pygame.Rect(SCREEN_WIDTH // 2 - 270, 130, 540, 310)
                if not modal_box.collidepoint(mouse_pos):
                    self.active_modal = None

            return None, state

        # 4. Standard In-Level Inputs
        if event.type == pygame.KEYDOWN:
            # Return to Hub
            if event.key in (pygame.K_ESCAPE, pygame.K_h):
                return "return_to_hub", state

            # Interaction Key [E]
            elif event.key == pygame.K_e:
                # Check if near hidden secret
                if self._is_near_secret():
                    if not has_flag(state, FLAG_KNOWS_SANA_CONTACT):
                        new_state = self.investigate_secret(state)
                        return None, new_state
                    else:
                        self.secret_dialog_open = True
                        return None, state

                # Check if near physical station
                station = self._get_nearby_station()
                if station:
                    self.active_modal = station.category
                    self.modal_selection_idx = (
                        self.selected_route_idx
                        if station.category == "route"
                        else (
                            self.selected_timing_idx
                            if station.category == "timing"
                            else self.selected_tool_idx or 0
                        )
                    ) or 0
                    return None, state

            # Execute plan shortcut
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                if self.is_plan_complete():
                    self.plan_executed_dialog = True
                    return None, state

            # Quick number keys to open corresponding category
            elif event.key == pygame.K_1:
                self.active_modal = "route"
                self.modal_selection_idx = self.selected_route_idx or 0
            elif event.key == pygame.K_2:
                self.active_modal = "timing"
                self.modal_selection_idx = self.selected_timing_idx or 0
            elif event.key == pygame.K_3:
                self.active_modal = "tool"
                self.modal_selection_idx = self.selected_tool_idx or 0

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Top Hub button
            if self.btn_hub_rect.collidepoint(mouse_pos):
                return "return_to_hub", state

            # Board category slots click
            for cat, rect in self.board_slot_rects.items():
                if rect.collidepoint(mouse_pos):
                    self.active_modal = cat
                    self.modal_selection_idx = (
                        self.selected_route_idx
                        if cat == "route"
                        else (
                            self.selected_timing_idx
                            if cat == "timing"
                            else self.selected_tool_idx or 0
                        )
                    ) or 0
                    return None, state

            # Physical Stations click
            for station in self.stations:
                if station.rect.collidepoint(mouse_pos):
                    self.active_modal = station.category
                    self.modal_selection_idx = (
                        self.selected_route_idx
                        if station.category == "route"
                        else (
                            self.selected_timing_idx
                            if station.category == "timing"
                            else self.selected_tool_idx or 0
                        )
                    ) or 0
                    return None, state

            # Hidden Secret click
            if self.secret_rect.collidepoint(mouse_pos) or self._is_near_secret():
                if not has_flag(state, FLAG_KNOWS_SANA_CONTACT):
                    new_state = self.investigate_secret(state)
                    return None, new_state
                else:
                    self.secret_dialog_open = True
                    return None, state

            # Execute Plan button click
            if self.btn_execute_rect.collidepoint(mouse_pos) and self.is_plan_complete():
                self.plan_executed_dialog = True
                return None, state

        return None, state

    def update(self, dt: float):
        """Update simulation and animations."""
        self.ambient_time += dt

        # Update toast notification timer
        if self.secret_toast_timer > 0:
            self.secret_toast_timer = max(0.0, self.secret_toast_timer - dt)

        # Allow player movement only when modal / dialogs are closed
        if not (self.active_modal or self.secret_dialog_open or self.plan_executed_dialog):
            self.all_sprites.update(dt)

            # Clamp player to safehouse playable room interior
            self.player.rect.left = max(25, self.player.rect.left)
            self.player.rect.right = min(SCREEN_WIDTH - 25, self.player.rect.right)
            self.player.rect.top = max(215, self.player.rect.top)
            self.player.rect.bottom = min(SCREEN_HEIGHT - 35, self.player.rect.bottom)
            self.player.pos = pygame.math.Vector2(self.player.rect.center)

    def draw(self, surface: pygame.Surface, state: GameState):
        """Render the safehouse room, planning corkboard, stations, and modals."""
        surface.fill(COLOR_BACKGROUND)

        # 1. Draw Safehouse Room Architecture & Floor
        self._draw_safehouse_floor(surface)

        # 2. Draw Physical Stations
        self._draw_stations(surface)

        # 3. Draw Hidden Secret Detail (Sana's Burner Radio)
        self._draw_secret_object(surface, state)

        # 4. Draw Player Character
        self.all_sprites.draw(surface)

        # 5. Draw Proximity Interaction Prompts
        self._draw_proximity_prompts(surface, state)

        # 6. Draw Master Planning Board (Header & Slots)
        self._draw_planning_board(surface)

        # 7. Draw Secret Toast Notification (if recently discovered)
        if self.secret_toast_timer > 0:
            self._draw_secret_toast(surface)

        # 8. Draw Active Modals & Dialogs (if open)
        if self.active_modal in ("route", "timing", "tool"):
            self._draw_choice_modal(surface)
        elif self.secret_dialog_open:
            self._draw_secret_dialog(surface)
        elif self.plan_executed_dialog:
            self._draw_execution_confirmation(surface, state)

        # 9. Top Navigation & Footer Hints
        self._draw_hud_overlays(surface)

    def _draw_safehouse_floor(self, surface: pygame.Surface):
        """Draw safehouse floor grid, walls, and lighting boundaries."""
        # Top concrete wall barrier
        wall_rect = pygame.Rect(20, 205, SCREEN_WIDTH - 40, 8)
        pygame.draw.rect(surface, (40, 48, 64), wall_rect, border_radius=4)

        # Subtle ambient grid lines on the concrete floor
        grid_color = (25, 30, 42)
        for x in range(30, SCREEN_WIDTH - 30, 50):
            pygame.draw.line(surface, grid_color, (x, 215), (x, SCREEN_HEIGHT - 40))
        for y in range(215, SCREEN_HEIGHT - 40, 50):
            pygame.draw.line(surface, grid_color, (30, y), (SCREEN_WIDTH - 30, y))

    def _draw_planning_board(self, surface: pygame.Surface):
        """Draw corkboard with 3 category slots (Route, Timing, Tool)."""
        mouse_pos = pygame.mouse.get_pos()

        # Board container outline
        board_rect = pygame.Rect(20, 60, SCREEN_WIDTH - 40, 142)
        pygame.draw.rect(surface, (28, 34, 46), board_rect, border_radius=8)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, board_rect, width=1, border_radius=8)

        # 3 Category Slots
        slots_data = [
            ("route", "1. INFILTRATION ROUTE", self.selected_route_idx, ROUTE_CHOICES, (70, 150, 240)),
            ("timing", "2. SECURITY TIMING", self.selected_timing_idx, TIMING_CHOICES, (240, 160, 50)),
            ("tool", "3. VAULT TOOL", self.selected_tool_idx, TOOL_CHOICES, (64, 200, 120)),
        ]

        for cat_key, cat_title, sel_idx, choices_list, cat_color in slots_data:
            slot_rect = self.board_slot_rects[cat_key]
            is_hover = slot_rect.collidepoint(mouse_pos)
            is_set = sel_idx is not None

            bg_col = COLOR_CARD_HOVER if is_hover else COLOR_CARD_BG
            border_col = cat_color if is_set else (COLOR_SELECTED if is_hover else COLOR_CARD_BORDER)

            pygame.draw.rect(surface, bg_col, slot_rect, border_radius=6)
            pygame.draw.rect(surface, border_col, slot_rect, width=2 if is_set else 1, border_radius=6)

            # Header inside card
            title_surf = self.board_title_font.render(cat_title, True, cat_color)
            surface.blit(title_surf, (slot_rect.x + 12, slot_rect.y + 10))

            # Value label
            if is_set:
                chosen_name = choices_list[sel_idx][0]
                val_surf = self.board_val_font.render(chosen_name, True, COLOR_TEXT)
                sub_hint = self.prompt_font.render("✓ LOCKED IN (Click to change)", True, COLOR_COMPLETED)
            else:
                val_surf = self.board_val_font.render("[ NOT CHOSEN ]", True, COLOR_MUTED)
                sub_hint = self.prompt_font.render("◄ Click or inspect station", True, (160, 170, 185))

            surface.blit(val_surf, (slot_rect.x + 12, slot_rect.y + 30))
            surface.blit(sub_hint, (slot_rect.x + 12, slot_rect.y + 50))

        # Finalize / Execute Plan button
        all_chosen = self.is_plan_complete()
        exec_hover = self.btn_execute_rect.collidepoint(mouse_pos)

        if all_chosen:
            exec_bg = (40, 90, 55) if exec_hover else (30, 70, 45)
            exec_border = COLOR_COMPLETED
            exec_text = "★ EXECUTE PLAN (SPACE / Click) ★"
            exec_color = COLOR_COMPLETED
        else:
            exec_bg = (32, 38, 50)
            exec_border = COLOR_CARD_BORDER
            exec_text = "Select all 3 options to execute plan"
            exec_color = COLOR_MUTED

        pygame.draw.rect(surface, exec_bg, self.btn_execute_rect, border_radius=6)
        pygame.draw.rect(surface, exec_border, self.btn_execute_rect, width=2 if all_chosen else 1, border_radius=6)
        exec_surf = self.prompt_font.render(exec_text, True, exec_color)
        surface.blit(exec_surf, exec_surf.get_rect(center=self.btn_execute_rect.center))

    def _draw_stations(self, surface: pygame.Surface):
        """Draw the physical stations inside the safehouse room."""
        for station in self.stations:
            # Table body
            pygame.draw.rect(surface, (34, 42, 58), station.rect, border_radius=8)
            pygame.draw.rect(surface, station.accent_color, station.rect, width=2, border_radius=8)

            # Top icon / accent pill
            pill = pygame.Rect(station.rect.x + 8, station.rect.y + 8, station.rect.width - 16, 16)
            pygame.draw.rect(surface, (25, 32, 45), pill, border_radius=4)

            # Station Name
            lbl_surf = self.station_font.render(station.label, True, station.accent_color)
            surface.blit(lbl_surf, (station.rect.x + 10, station.rect.y + 32))

            name_surf = self.modal_desc_font.render(station.name, True, COLOR_TEXT)
            surface.blit(name_surf, (station.rect.x + 10, station.rect.y + 52))

    def _draw_secret_object(self, surface: pygame.Surface, state: GameState):
        """Draw the hidden burner radio in the bottom-left corner."""
        knows_secret = has_flag(state, FLAG_KNOWS_SANA_CONTACT)

        # Crate / desk background
        pygame.draw.rect(surface, (28, 32, 42), self.secret_rect, border_radius=6)
        border_col = COLOR_COMPLETED if knows_secret else (55, 65, 85)
        pygame.draw.rect(surface, border_col, self.secret_rect, width=1, border_radius=6)

        # Blinking LED on radio device
        led_pulse = (math.sin(self.ambient_time * 5.0) + 1.0) / 2.0
        if knows_secret:
            led_color = (64, 200, 120)
        else:
            led_color = (int(50 + 205 * led_pulse), int(140 + 80 * led_pulse), 240)

        pygame.draw.circle(surface, led_color, (self.secret_rect.centerx, self.secret_rect.centery - 4), 6)

        # Label under secret
        tag_text = "Burner Comms" if knows_secret else "Tucked Crate"
        tag_surf = self.modal_desc_font.render(tag_text, True, COLOR_MUTED)
        surface.blit(tag_surf, tag_surf.get_rect(center=(self.secret_rect.centerx, self.secret_rect.bottom + 10)))

    def _draw_proximity_prompts(self, surface: pygame.Surface, state: GameState):
        """Draw floating prompt when player is within interaction range."""
        player_midtop = self.player.rect.midtop

        # Near secret detail
        if self._is_near_secret():
            if not has_flag(state, FLAG_KNOWS_SANA_CONTACT):
                prompt_text = "[E] Investigate Discarded Radio Device"
                prompt_color = (100, 200, 255)
            else:
                prompt_text = "[E] Review Sana's Frequency Note"
                prompt_color = COLOR_COMPLETED

            p_surf = self.prompt_font.render(prompt_text, True, prompt_color)
            p_rect = p_surf.get_rect(midbottom=(player_midtop[0], player_midtop[1] - 8))
            bg_rect = p_rect.inflate(12, 6)
            pygame.draw.rect(surface, (20, 25, 35), bg_rect, border_radius=4)
            pygame.draw.rect(surface, prompt_color, bg_rect, width=1, border_radius=4)
            surface.blit(p_surf, p_rect)
            return

        # Near station
        station = self._get_nearby_station()
        if station:
            prompt_text = f"[E] Examine {station.name}"
            p_surf = self.prompt_font.render(prompt_text, True, station.accent_color)
            p_rect = p_surf.get_rect(midbottom=(player_midtop[0], player_midtop[1] - 8))
            bg_rect = p_rect.inflate(12, 6)
            pygame.draw.rect(surface, (20, 25, 35), bg_rect, border_radius=4)
            pygame.draw.rect(surface, station.accent_color, bg_rect, width=1, border_radius=4)
            surface.blit(p_surf, p_rect)

    def _draw_choice_modal(self, surface: pygame.Surface):
        """Render the modal dialog showing 3 choices for the active category."""
        modal_w, modal_h = 560, 310
        modal_rect = pygame.Rect(
            (SCREEN_WIDTH - modal_w) // 2, (SCREEN_HEIGHT - modal_h) // 2 + 10, modal_w, modal_h
        )

        # Dim overlay
        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 160))
        surface.blit(dim_surf, (0, 0))

        # Modal Window Box
        pygame.draw.rect(surface, (24, 30, 42), modal_rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_SELECTED, modal_rect, width=2, border_radius=10)

        # Modal Title
        cat_title = (
            "CHOOSE INFILTRATION ROUTE"
            if self.active_modal == "route"
            else ("CHOOSE TIMING WINDOW" if self.active_modal == "timing" else "CHOOSE VAULT TOOL")
        )
        title_surf = self.modal_title_font.render(cat_title, True, COLOR_SELECTED)
        surface.blit(title_surf, (modal_rect.x + 25, modal_rect.y + 18))

        close_hint = self.modal_desc_font.render("[ESC] or Click outside to close", True, COLOR_MUTED)
        surface.blit(close_hint, (modal_rect.right - close_hint.get_width() - 25, modal_rect.y + 22))

        # Choices
        choices = (
            ROUTE_CHOICES
            if self.active_modal == "route"
            else (TIMING_CHOICES if self.active_modal == "timing" else TOOL_CHOICES)
        )
        current_sel = (
            self.selected_route_idx
            if self.active_modal == "route"
            else (
                self.selected_timing_idx
                if self.active_modal == "timing"
                else self.selected_tool_idx
            )
        )

        mouse_pos = pygame.mouse.get_pos()
        card_y = modal_rect.y + 55

        for idx, (title, desc) in enumerate(choices):
            opt_rect = pygame.Rect(modal_rect.x + 25, card_y + idx * 76, modal_w - 50, 66)
            is_hover = opt_rect.collidepoint(mouse_pos)
            is_active = idx == self.modal_selection_idx
            is_chosen = idx == current_sel

            if is_chosen:
                bg_col = (30, 55, 42)
                border_col = COLOR_COMPLETED
            elif is_hover or is_active:
                bg_col = COLOR_CARD_HOVER
                border_col = COLOR_SELECTED
            else:
                bg_col = COLOR_CARD_BG
                border_col = COLOR_CARD_BORDER

            pygame.draw.rect(surface, bg_col, opt_rect, border_radius=6)
            pygame.draw.rect(surface, border_col, opt_rect, width=2 if (is_hover or is_chosen) else 1, border_radius=6)

            # Option title
            label_text = f"[{idx + 1}]  {title}"
            title_color = COLOR_COMPLETED if is_chosen else COLOR_TEXT
            opt_title_surf = self.modal_opt_font.render(label_text, True, title_color)
            surface.blit(opt_title_surf, (opt_rect.x + 14, opt_rect.y + 10))

            if is_chosen:
                badge = self.prompt_font.render("✓ SELECTED", True, COLOR_COMPLETED)
                surface.blit(badge, (opt_rect.right - badge.get_width() - 14, opt_rect.y + 12))

            # Option description
            desc_surf = self.modal_desc_font.render(desc, True, (180, 190, 205))
            surface.blit(desc_surf, (opt_rect.x + 14, opt_rect.y + 36))

    def _draw_secret_dialog(self, surface: pygame.Surface):
        """Render secret discovery dialogue when investigating the burner radio."""
        diag_w, diag_h = 580, 240
        diag_rect = pygame.Rect(
            (SCREEN_WIDTH - diag_w) // 2, (SCREEN_HEIGHT - diag_h) // 2, diag_w, diag_h
        )

        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 170))
        surface.blit(dim_surf, (0, 0))

        pygame.draw.rect(surface, (20, 26, 38), diag_rect, border_radius=10)
        pygame.draw.rect(surface, (80, 180, 255), diag_rect, width=2, border_radius=10)

        title_surf = self.modal_title_font.render("★ HIDDEN CLUE: DISCARDED COMMS RADIO", True, (100, 210, 255))
        surface.blit(title_surf, (diag_rect.x + 25, diag_rect.y + 20))

        body_lines = [
            "Tucked behind the server rack, you inspect a modified transceiver.",
            "Scratched into the casing is an encrypted frequency code and a warning:",
            "",
            "    \"SANA — SECURE FREQ 142.85 MHz. DON'T TRUST KABIR'S LEDGER.\"",
            "",
            "You log Sana's direct backchannel into your cipher notepad.",
        ]
        curr_y = diag_rect.y + 58
        for line in body_lines:
            col = COLOR_FINALE if "SANA" in line else COLOR_TEXT
            font = self.modal_opt_font if "SANA" in line else self.modal_desc_font
            line_surf = font.render(line, True, col)
            surface.blit(line_surf, (diag_rect.x + 25, curr_y))
            curr_y += 22

        btn_text = "[ Press E, SPACE, or Click to Continue ]"
        btn_surf = self.prompt_font.render(btn_text, True, COLOR_COMPLETED)
        surface.blit(btn_surf, btn_surf.get_rect(center=(diag_rect.centerx, diag_rect.bottom - 24)))

    def _draw_execution_confirmation(self, surface: pygame.Surface, state: GameState):
        """Render plan completion confirmation popup before returning to hub."""
        diag_w, diag_h = 560, 270
        diag_rect = pygame.Rect(
            (SCREEN_WIDTH - diag_w) // 2, (SCREEN_HEIGHT - diag_h) // 2, diag_w, diag_h
        )

        dim_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim_surf.fill((0, 0, 0, 180))
        surface.blit(dim_surf, (0, 0))

        pygame.draw.rect(surface, (20, 32, 28), diag_rect, border_radius=10)
        pygame.draw.rect(surface, COLOR_COMPLETED, diag_rect, width=2, border_radius=10)

        title_surf = self.modal_title_font.render("★ HEIST PLAN SOLIDIFIED ★", True, COLOR_COMPLETED)
        surface.blit(title_surf, title_surf.get_rect(center=(diag_rect.centerx, diag_rect.y + 28)))

        route_name = ROUTE_CHOICES[self.selected_route_idx][0]
        timing_name = TIMING_CHOICES[self.selected_timing_idx][0]
        tool_name = TOOL_CHOICES[self.selected_tool_idx][0]
        has_sana = has_flag(state, FLAG_KNOWS_SANA_CONTACT)

        summary_lines = [
            f"• Route:  {route_name}",
            f"• Timing: {timing_name}",
            f"• Tool:   {tool_name}",
            "",
            "★ Sana's Private Comms Acquired" if has_sana else "○ Sana's Private Comms Undiscovered",
            "",
            "Kabir reviews the corkboard and nods: 'The plan is set. Move out.'",
        ]

        curr_y = diag_rect.y + 60
        for line in summary_lines:
            col = COLOR_FINALE if "★" in line else (COLOR_MUTED if "○" in line else COLOR_TEXT)
            line_surf = self.modal_desc_font.render(line, True, col)
            surface.blit(line_surf, (diag_rect.x + 35, curr_y))
            curr_y += 22

        btn_text = "Press SPACE / Click to Complete Chapter & Return to Hub"
        btn_surf = self.prompt_font.render(btn_text, True, COLOR_COMPLETED)
        surface.blit(btn_surf, btn_surf.get_rect(center=(diag_rect.centerx, diag_rect.bottom - 25)))

    def _draw_secret_toast(self, surface: pygame.Surface):
        """Render temporary banner in top center when secret is unlocked."""
        toast_w, toast_h = 480, 32
        toast_rect = pygame.Rect((SCREEN_WIDTH - toast_w) // 2, 20, toast_w, toast_h)
        pygame.draw.rect(surface, (20, 50, 40), toast_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_COMPLETED, toast_rect, width=1, border_radius=6)

        toast_text = "★ SECRET LOGGED: Sana's Contact Acquired (+knows_sana_contact) ★"
        t_surf = self.prompt_font.render(toast_text, True, COLOR_COMPLETED)
        surface.blit(t_surf, t_surf.get_rect(center=toast_rect.center))

    def _draw_hud_overlays(self, surface: pygame.Surface):
        """Top bar return button and bottom controls reminder."""
        mouse_pos = pygame.mouse.get_pos()

        # Top Return to Hub button
        hub_hover = self.btn_hub_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, COLOR_CARD_HOVER if hub_hover else COLOR_CARD_BG, self.btn_hub_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.btn_hub_rect, width=1, border_radius=6)
        btn_text = self.modal_desc_font.render("◄ [H] Return to Hub", True, COLOR_TEXT)
        surface.blit(btn_text, btn_text.get_rect(center=self.btn_hub_rect.center))

        # Level Title
        lvl_title = self.title_font.render("CHAPTER 1: THE PLAN", True, COLOR_SELECTED)
        surface.blit(lvl_title, (SCREEN_WIDTH // 2 - lvl_title.get_width() // 2, 22))

        # Bottom Instructions
        footer_text = "WASD/Arrows: Move  |  [E]: Interact with Stations & Objects  |  1/2/3: Quick Select  |  Mouse Supported"
        footer_surf = self.footer_font.render(footer_text, True, COLOR_MUTED)
        surface.blit(footer_surf, footer_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 16)))
