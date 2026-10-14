"""The Watcher - Playable surveillance level.

The player observes a guard's patrol pattern from a rooftop vantage point across
3 in-game days without getting caught by the sweeping searchlight.
At a scripted moment during Day 2, observing the Back Service Alley reveals Kabir
meeting an unfamiliar contact, setting the 'knows_kabir_meeting' flag.
Being spotted resets the current day attempt without exiting the chapter.
Completing all 3 days calls complete_chapter(state, 'The Watcher') and returns to the Hub.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
import pygame

from game_state import (
    CHAPTER_THE_WATCHER,
    FLAG_KNOWS_KABIR_MEETING,
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
    COLOR_FINALE,
    COLOR_MUTED,
    COLOR_SELECTED,
    COLOR_TEXT,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)


@dataclass
class ObservationZone:
    """A vantage point sector along the rooftop edge overlooking the facility."""

    id_name: str
    label: str
    rect: pygame.Rect  # Rooftop interaction area
    target_rect: pygame.Rect  # Ground area observed
    accent_color: Tuple[int, int, int]


class TheWatcherLevel:
    """Manages Chapter 2: The Watcher surveillance gameplay and stealth simulation."""

    def __init__(self):
        # Interactive player sprite on the observation rooftop
        self.all_sprites = pygame.sprite.Group()
        self.player = Player(SCREEN_WIDTH // 2, 490)
        self.all_sprites.add(self.player)

        # 3 In-Game Days System
        self.total_days: int = 3
        self.current_day: int = 1
        self.day_progress: float = 0.0  # 0.0 to 100.0%
        self.day_duration_sec: float = 14.0  # Approx seconds of observation per day

        # Stealth & Detection
        self.detection_level: float = 0.0  # 0.0 to 100.0%
        self.is_spotted: bool = False
        self.spotted_reset_timer: float = 0.0

        # Guard Patrol Simulation
        self.guard_pos = pygame.math.Vector2(120, 260)
        self.guard_dir = 1.0  # 1.0 moving right, -1.0 moving left
        self.guard_speed = 110.0
        self.searchlight_angle = 0.0  # Oscillates to sweep rooftop

        # Scripted Kabir Meeting Event (Occurs Day 2 between 30% and 75% progress)
        self.meeting_active: bool = False
        self.meeting_witnessed: bool = False
        self.meeting_dialog_open: bool = False
        self.toast_timer: float = 0.0
        self.toast_message: str = ""

        # Completion Dialog
        self.completed_dialog_open: bool = False

        # Observation Zones along the parapet (y=410 to 455)
        self.zones: List[ObservationZone] = [
            ObservationZone(
                id_name="gate",
                label="Zone 1: Main Gate & Perimeter",
                rect=pygame.Rect(50, 410, 210, 50),
                target_rect=pygame.Rect(50, 110, 210, 230),
                accent_color=(70, 150, 240),
            ),
            ObservationZone(
                id_name="courtyard",
                label="Zone 2: Vault Exterior Courtyard",
                rect=pygame.Rect(295, 410, 210, 50),
                target_rect=pygame.Rect(295, 110, 210, 230),
                accent_color=(235, 160, 40),
            ),
            ObservationZone(
                id_name="alley",
                label="Zone 3: Back Service Alley",
                rect=pygame.Rect(540, 410, 210, 50),
                target_rect=pygame.Rect(540, 110, 210, 230),
                accent_color=(64, 200, 120),
            ),
        ]

        # Buttons
        self.btn_hub_rect = pygame.Rect(25, 18, 140, 34)

        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 20, bold=True)
        self.header_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 14, bold=True)
        self.status_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13)
        self.prompt_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.dialog_title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)
        self.dialog_body_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 14)

    def reset(self):
        """Reset surveillance attempt to Day 1."""
        self.current_day = 1
        self.day_progress = 0.0
        self.detection_level = 0.0
        self.is_spotted = False
        self.spotted_reset_timer = 0.0
        self.meeting_active = False
        self.meeting_witnessed = False
        self.meeting_dialog_open = False
        self.completed_dialog_open = False
        self.toast_timer = 0.0
        self.guard_pos = pygame.math.Vector2(120, 260)
        self.guard_dir = 1.0
        self.player.rect.center = (SCREEN_WIDTH // 2, 490)
        self.player.pos = pygame.math.Vector2(self.player.rect.center)

    def reset_current_day(self):
        """Reset progress for the current day after being spotted."""
        self.day_progress = 0.0
        self.detection_level = 0.0
        self.is_spotted = False
        self.spotted_reset_timer = 0.0
        self.meeting_active = False
        # Move player safely back into cover
        self.player.rect.center = (SCREEN_WIDTH // 2, 500)
        self.player.pos = pygame.math.Vector2(self.player.rect.center)
        self.guard_pos = pygame.math.Vector2(120, 260)
        self.guard_dir = 1.0

    def is_in_cover(self) -> bool:
        """Player is in cover when stepped back from the parapet edge (y >= 465)."""
        return self.player.rect.centery >= 465

    def is_observing(self) -> bool:
        """Player is actively observing when standing at the parapet edge (y < 465)."""
        return self.player.rect.centery < 465 and not self.is_spotted

    def get_active_zone(self) -> Optional[ObservationZone]:
        """Return the observation zone the player is currently occupying, if any."""
        player_x = self.player.rect.centerx
        for zone in self.zones:
            if zone.rect.left <= player_x <= zone.rect.right:
                return zone
        return None

    def trigger_spotted(self):
        """Trigger spotted state, penalizing the attempt and preparing a reset."""
        self.is_spotted = True
        self.detection_level = 100.0
        self.spotted_reset_timer = 1.8

    def witness_kabir_meeting(self, state: GameState) -> GameState:
        """Record witnessing Kabir's secret meeting and update GameState."""
        self.meeting_witnessed = True
        self.meeting_dialog_open = True
        self.toast_timer = 4.0
        self.toast_message = "★ SURVEILLANCE LOGGED: Kabir's Secret Meeting Discovered (+knows_kabir_meeting)"
        return set_flag(state, FLAG_KNOWS_KABIR_MEETING)

    def complete_surveillance(self, state: GameState) -> Tuple[str, GameState]:
        """Complete Chapter 2: The Watcher and return to the Hub."""
        new_state = complete_chapter(state, CHAPTER_THE_WATCHER)
        new_state = set_current_chapter(new_state, None)
        return "return_to_hub", new_state

    def handle_event(
        self, event: pygame.event.Event, state: GameState
    ) -> Tuple[Optional[str], GameState]:
        """Process player inputs, navigation, and dialog dismissals."""
        # 1. Kabir Meeting Dialogue
        if self.meeting_dialog_open:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self.meeting_dialog_open = False
            return None, state

        # 2. Final Completion Dialogue
        if self.completed_dialog_open:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                return self.complete_surveillance(state)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self.complete_surveillance(state)
            return None, state

        # 3. Standard In-Level Inputs
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_ESCAPE, pygame.K_h):
                return "return_to_hub", state

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.btn_hub_rect.collidepoint(event.pos):
                return "return_to_hub", state

        return None, state

    def update(self, dt: float, state: Optional[GameState] = None) -> Optional[GameState]:
        """Update guard patrol, stealth detection, day progression, and scripted events."""
        # Countdown toast timer
        if self.toast_timer > 0:
            self.toast_timer = max(0.0, self.toast_timer - dt)

        # Handle spotted countdown reset
        if self.is_spotted:
            self.spotted_reset_timer -= dt
            if self.spotted_reset_timer <= 0:
                self.reset_current_day()
            return None

        # Pause game logic when dialogue is reading
        if self.meeting_dialog_open or self.completed_dialog_open:
            return None

        # 1. Update Player Movement & Bounds
        self.all_sprites.update(dt)
        self.player.rect.left = max(45, self.player.rect.left)
        self.player.rect.right = min(SCREEN_WIDTH - 45, self.player.rect.right)
        self.player.rect.top = max(415, self.player.rect.top)
        self.player.rect.bottom = min(SCREEN_HEIGHT - 35, self.player.rect.bottom)
        self.player.pos = pygame.math.Vector2(self.player.rect.center)

        # 2. Update Guard Patrol
        self.guard_pos.x += self.guard_dir * self.guard_speed * dt
        if self.guard_pos.x >= SCREEN_WIDTH - 140:
            self.guard_pos.x = SCREEN_WIDTH - 140
            self.guard_dir = -1.0
        elif self.guard_pos.x <= 120:
            self.guard_pos.x = 120
            self.guard_dir = 1.0

        # Oscillating searchlight angle
        self.searchlight_angle = math.sin(pygame.time.get_ticks() / 600.0)

        # 3. Stealth & Detection Calculation
        # The guard's searchlight illuminates the rooftop area directly above and slightly angled
        guard_beam_center_x = self.guard_pos.x + self.searchlight_angle * 120.0
        beam_radius = 95.0

        is_illuminated = (
            abs(self.player.rect.centerx - guard_beam_center_x) < beam_radius
        )

        if not self.is_in_cover() and is_illuminated:
            # Player is exposed at the edge under the searchlight!
            self.detection_level = min(100.0, self.detection_level + dt * 110.0)
            if self.detection_level >= 100.0:
                self.trigger_spotted()
                return None
        else:
            # In cover or outside beam: detection cools down
            self.detection_level = max(0.0, self.detection_level - dt * 65.0)

        # 4. Day Observation Progress
        if self.is_observing():
            progress_speed = 100.0 / self.day_duration_sec
            self.day_progress = min(100.0, self.day_progress + progress_speed * dt)

        # 5. Scripted Kabir Meeting Event (Day 2 between 30% and 75% progress)
        if self.current_day == 2:
            if 30.0 <= self.day_progress <= 75.0:
                self.meeting_active = True
                # If player is observing in Zone 3 (Back Alley), witness the meeting!
                active_zone = self.get_active_zone()
                if (
                    self.is_observing()
                    and active_zone is not None
                    and active_zone.id_name == "alley"
                    and not self.meeting_witnessed
                ):
                    if state is not None:
                        return self.witness_kabir_meeting(state)
                    else:
                        self.meeting_witnessed = True
                        self.meeting_dialog_open = True
            else:
                self.meeting_active = False

        # 6. Day Transition or Chapter Completion
        if self.day_progress >= 100.0:
            if self.current_day < self.total_days:
                self.current_day += 1
                self.day_progress = 0.0
                self.detection_level = 0.0
                self.toast_timer = 3.0
                self.toast_message = f"Day {self.current_day - 1} Complete! Beginning Day {self.current_day} observation..."
            else:
                self.completed_dialog_open = True

        return None

    def draw(self, surface: pygame.Surface, state: GameState):
        """Render the rooftop surveillance scene, guard ground patrol, and stealth UI."""
        surface.fill(COLOR_BACKGROUND)

        # 1. Ground Facility View (Top half, y=60 to 400)
        self._draw_ground_facility(surface)

        # 2. Guard & Sweeping Searchlight Beam
        self._draw_guard_and_light(surface)

        # 3. Scripted Kabir Meeting Scene (if active)
        if self.meeting_active:
            self._draw_kabir_meeting(surface)

        # 4. Rooftop Vantage Architecture (Bottom half, y=400 to 600)
        self._draw_rooftop_deck(surface)

        # 5. Player Character Sprite
        self.all_sprites.draw(surface)

        # 6. Interaction Prompts and Zone Status
        self._draw_surveillance_hud(surface, state)

        # 7. Red Spotted Vignette Overlay (if detected)
        if self.is_spotted:
            self._draw_spotted_overlay(surface)

        # 8. Dialogues (Kabir meeting discovery or mission completion)
        if self.meeting_dialog_open:
            self._draw_meeting_dialog(surface)
        elif self.completed_dialog_open:
            self._draw_completed_dialog(surface, state)

        # 9. Toast Notification Banner
        if self.toast_timer > 0:
            self._draw_toast(surface)

        # 10. Top Bar Overlays
        self._draw_top_bar(surface)

    def _draw_ground_facility(self, surface: pygame.Surface):
        """Draw the target compound grounds, fence, gates, and alleyway."""
        ground_rect = pygame.Rect(25, 65, SCREEN_WIDTH - 50, 335)
        pygame.draw.rect(surface, (18, 22, 30), ground_rect)
        pygame.draw.rect(surface, (35, 45, 60), ground_rect, width=1)

        # Grid lines on asphalt
        for x in range(50, SCREEN_WIDTH - 50, 60):
            pygame.draw.line(surface, (23, 29, 40), (x, 70), (x, 395))

        # Zone boundaries and visual landmarks
        for zone in self.zones:
            # Subtle boundary tint
            pygame.draw.rect(surface, (25, 34, 48), zone.target_rect, border_radius=4)
            pygame.draw.rect(surface, (40, 52, 70), zone.target_rect, width=1, border_radius=4)

            # Zone Ground Label
            lbl_surf = self.status_font.render(zone.label.split(":")[1].strip(), True, zone.accent_color)
            surface.blit(lbl_surf, (zone.target_rect.x + 12, zone.target_rect.y + 10))

        # Vault doors in Zone 2
        vault_door = pygame.Rect(355, 95, 90, 24)
        pygame.draw.rect(surface, (50, 62, 85), vault_door, border_radius=4)
        pygame.draw.rect(surface, (80, 100, 135), vault_door, width=2, border_radius=4)

        # Main gate in Zone 1
        gate_rect = pygame.Rect(75, 95, 80, 18)
        pygame.draw.rect(surface, (45, 55, 75), gate_rect, border_radius=3)

    def _draw_guard_and_light(self, surface: pygame.Surface):
        """Render the patrolling guard sprite and sweeping searchlight beam."""
        guard_x = int(self.guard_pos.x)
        guard_y = int(self.guard_pos.y)

        # Guard Body (Red/White uniform marker)
        pygame.draw.circle(surface, (220, 60, 60), (guard_x, guard_y), 10)
        pygame.draw.circle(surface, (255, 255, 255), (guard_x, guard_y), 10, width=2)

        # Facing direction indicator
        nose_x = guard_x + int(self.guard_dir * 12)
        pygame.draw.line(surface, (255, 255, 255), (guard_x, guard_y), (nose_x, guard_y), 3)

        # Searchlight Beam sweeping upward toward the rooftop
        beam_top_center_x = guard_x + int(self.searchlight_angle * 140)
        beam_top_y = 410
        beam_width = 170

        beam_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        beam_poly = [
            (guard_x, guard_y),
            (beam_top_center_x - beam_width // 2, beam_top_y),
            (beam_top_center_x + beam_width // 2, beam_top_y),
        ]
        # Yellow translucent flashlight cone
        pygame.draw.polygon(beam_surf, (255, 240, 120, 48), beam_poly)
        pygame.draw.polygon(beam_surf, (255, 240, 150, 90), beam_poly, width=1)
        surface.blit(beam_surf, (0, 0))

    def _draw_kabir_meeting(self, surface: pygame.Surface):
        """Render Kabir and the unknown contact in the Back Service Alley during Day 2."""
        alley_x = 640
        alley_y = 170

        # Streetlamp cone
        lamp_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.circle(lamp_surf, (255, 220, 120, 60), (alley_x, alley_y), 38)
        surface.blit(lamp_surf, (0, 0))

        # Kabir Figure (Emerald green badge)
        pygame.draw.circle(surface, (64, 200, 120), (alley_x - 14, alley_y), 9)
        # Unfamiliar Contact (Trenchcoated shadowed figure)
        pygame.draw.circle(surface, (160, 140, 220), (alley_x + 14, alley_y), 9)

        # Briefcase exchange icon
        case_rect = pygame.Rect(alley_x - 4, alley_y - 4, 8, 8)
        pygame.draw.rect(surface, COLOR_FINALE, case_rect)

        # Alert banner pointing toward the alley
        hint_text = "★ UNIDENTIFIED MEETING IN PROGRESS ★"
        hint_surf = self.status_font.render(hint_text, True, COLOR_FINALE)
        surface.blit(hint_surf, (alley_x - hint_surf.get_width() // 2, alley_y - 32))

    def _draw_rooftop_deck(self, surface: pygame.Surface):
        """Render the rooftop observation deck, parapet wall, and cover areas."""
        deck_rect = pygame.Rect(25, 410, SCREEN_WIDTH - 50, 180)
        pygame.draw.rect(surface, (26, 32, 44), deck_rect)
        pygame.draw.rect(surface, (50, 62, 82), deck_rect, width=2)

        # Parapet edge line (Observation boundary)
        pygame.draw.line(surface, (80, 100, 130), (25, 460), (SCREEN_WIDTH - 25, 460), 2)

        # Cover zone label
        cover_lbl = self.status_font.render("◄ COVER ZONE (Safe from Searchlight) ►", True, (90, 110, 140))
        surface.blit(cover_lbl, cover_lbl.get_rect(center=(SCREEN_WIDTH // 2, 575)))

        # 3 Observation Zone Markers along the parapet
        for zone in self.zones:
            is_active = zone.rect.collidepoint(self.player.rect.center)
            border_col = zone.accent_color if is_active else (50, 65, 88)

            pygame.draw.rect(surface, (32, 40, 56), zone.rect, border_radius=4)
            pygame.draw.rect(surface, border_col, zone.rect, width=2 if is_active else 1, border_radius=4)

            # Zone label
            lbl = self.status_font.render(zone.label.split(":")[0], True, zone.accent_color)
            surface.blit(lbl, (zone.rect.x + 8, zone.rect.y + 6))

    def _draw_surveillance_hud(self, surface: pygame.Surface, state: GameState):
        """Render detection meter, day progress bar, and observation status."""
        active_zone = self.get_active_zone()
        in_cover = self.is_in_cover()

        # Day & Observation HUD Bar
        hud_bar_y = 368
        pygame.draw.rect(surface, (20, 26, 36), (35, hud_bar_y, SCREEN_WIDTH - 70, 36), border_radius=6)
        pygame.draw.rect(surface, (45, 58, 78), (35, hud_bar_y, SCREEN_WIDTH - 70, 36), width=1, border_radius=6)

        # Day & Progress
        day_str = f"DAY {self.current_day} / {self.total_days}"
        day_surf = self.header_font.render(day_str, True, COLOR_TEXT)
        surface.blit(day_surf, (50, hud_bar_y + 9))

        # Progress bar
        bar_x = 160
        bar_w = 220
        pygame.draw.rect(surface, (35, 42, 56), (bar_x, hud_bar_y + 11, bar_w, 14), border_radius=4)
        fill_w = int(bar_w * (self.day_progress / 100.0))
        pygame.draw.rect(surface, COLOR_SELECTED, (bar_x, hud_bar_y + 11, fill_w, 14), border_radius=4)

        pct_surf = self.status_font.render(f"{int(self.day_progress)}%", True, COLOR_TEXT)
        surface.blit(pct_surf, (bar_x + bar_w + 10, hud_bar_y + 9))

        # Stealth Status / Detection Meter
        det_x = SCREEN_WIDTH - 300
        det_lbl = self.header_font.render("DETECTION:", True, COLOR_TEXT)
        surface.blit(det_lbl, (det_x, hud_bar_y + 9))

        det_bar_x = det_x + 95
        det_bar_w = 120
        pygame.draw.rect(surface, (35, 42, 56), (det_bar_x, hud_bar_y + 11, det_bar_w, 14), border_radius=4)

        det_fill_w = int(det_bar_w * (self.detection_level / 100.0))
        det_color = (240, 60, 60) if self.detection_level > 60 else (240, 180, 50)
        pygame.draw.rect(surface, det_color, (det_bar_x, hud_bar_y + 11, det_fill_w, 14), border_radius=4)

        # Player Status indicator above sprite
        if in_cover:
            stat_text = "[ IN COVER — HIDDEN ]"
            stat_col = (110, 180, 240)
        else:
            stat_text = f"[ OBSERVING: {active_zone.label.split(':')[0] if active_zone else 'PERIMETER'} ]"
            stat_col = COLOR_COMPLETED

        s_surf = self.prompt_font.render(stat_text, True, stat_col)
        surface.blit(s_surf, s_surf.get_rect(center=(self.player.rect.centerx, self.player.rect.top - 12)))

    def _draw_spotted_overlay(self, surface: pygame.Surface):
        """Render warning banner when detected by the guard."""
        spot_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        spot_surf.fill((180, 30, 30, 110))
        surface.blit(spot_surf, (0, 0))

        box_w, box_h = 520, 100
        box = pygame.Rect((SCREEN_WIDTH - box_w) // 2, (SCREEN_HEIGHT - box_h) // 2, box_w, box_h)
        pygame.draw.rect(surface, (30, 15, 15), box, border_radius=8)
        pygame.draw.rect(surface, (240, 60, 60), box, width=2, border_radius=8)

        warn_title = self.dialog_title_font.render("! SPOTTED BY GUARD !", True, (255, 80, 80))
        surface.blit(warn_title, warn_title.get_rect(center=(box.centerx, box.y + 32)))

        warn_sub = self.dialog_body_font.render(
            f"Resetting Day {self.current_day} attempt... Stay in cover when searchlight passes!", True, COLOR_TEXT
        )
        surface.blit(warn_sub, warn_sub.get_rect(center=(box.centerx, box.y + 68)))

    def _draw_meeting_dialog(self, surface: pygame.Surface):
        """Dialogue window triggered when witnessing Kabir's meeting."""
        diag_w, diag_h = 600, 260
        diag = pygame.Rect((SCREEN_WIDTH - diag_w) // 2, (SCREEN_HEIGHT - diag_h) // 2, diag_w, diag_h)

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 175))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (20, 26, 38), diag, border_radius=10)
        pygame.draw.rect(surface, COLOR_FINALE, diag, width=2, border_radius=10)

        title = self.dialog_title_font.render("★ INTEL UNCOVERED: KABIR'S RENDEZVOUS ★", True, COLOR_FINALE)
        surface.blit(title, (diag.x + 25, diag.y + 20))

        lines = [
            "You zoom your surveillance lenses onto the Back Service Alley...",
            "Under the flickering lamp, Kabir slips out to meet a stranger in a dark coat.",
            "",
            "    Unknown Contact: 'Here is the vault lock cipher. The crew takes the heat.'",
            "    Kabir:           'They suspect nothing. Stick to the drop point.'",
            "",
            "A confidential dossier changes hands. Kabir is setting up the crew!",
        ]
        curr_y = diag.y + 58
        for line in lines:
            col = COLOR_FINALE if "Kabir:" in line or "Unknown" in line else COLOR_TEXT
            surf = self.dialog_body_font.render(line, True, col)
            surface.blit(surf, (diag.x + 25, curr_y))
            curr_y += 22

        btn_surf = self.prompt_font.render("[ Press Any Key or Click to Continue Surveillance ]", True, COLOR_COMPLETED)
        surface.blit(btn_surf, btn_surf.get_rect(center=(diag.centerx, diag.bottom - 24)))

    def _draw_completed_dialog(self, surface: pygame.Surface, state: GameState):
        """Dialogue window upon successfully mapping all 3 days of patrol."""
        diag_w, diag_h = 560, 240
        diag = pygame.Rect((SCREEN_WIDTH - diag_w) // 2, (SCREEN_HEIGHT - diag_h) // 2, diag_w, diag_h)

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (20, 32, 28), diag, border_radius=10)
        pygame.draw.rect(surface, COLOR_COMPLETED, diag, width=2, border_radius=10)

        title = self.dialog_title_font.render("★ SURVEILLANCE COMPLETED ★", True, COLOR_COMPLETED)
        surface.blit(title, title.get_rect(center=(diag.centerx, diag.y + 28)))

        has_meeting = has_flag(state, FLAG_KNOWS_KABIR_MEETING)
        lines = [
            "All 3 days of security patrol patterns have been fully mapped.",
            "Guard blind spots, sweep intervals, and shift handovers logged.",
            "",
            "★ Kabir's Secret Meeting Logged" if has_meeting else "○ Kabir's Secret Meeting Undiscovered",
            "",
            "The crew has the exact patrol timetable needed for infiltration.",
        ]
        curr_y = diag.y + 60
        for line in lines:
            col = COLOR_FINALE if "★" in line else (COLOR_MUTED if "○" in line else COLOR_TEXT)
            surf = self.dialog_body_font.render(line, True, col)
            surface.blit(surf, (diag.x + 35, curr_y))
            curr_y += 22

        btn_surf = self.prompt_font.render("Press SPACE / Click to Complete Chapter & Return to Hub", True, COLOR_COMPLETED)
        surface.blit(btn_surf, btn_surf.get_rect(center=(diag.centerx, diag.bottom - 24)))

    def _draw_toast(self, surface: pygame.Surface):
        """Render top notification banner."""
        toast_w, toast_h = 580, 32
        toast_rect = pygame.Rect((SCREEN_WIDTH - toast_w) // 2, 20, toast_w, toast_h)
        pygame.draw.rect(surface, (20, 48, 38), toast_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_COMPLETED, toast_rect, width=1, border_radius=6)

        t_surf = self.prompt_font.render(self.toast_message, True, COLOR_COMPLETED)
        surface.blit(t_surf, t_surf.get_rect(center=toast_rect.center))

    def _draw_top_bar(self, surface: pygame.Surface):
        """Top return button and chapter header."""
        mouse_pos = pygame.mouse.get_pos()

        # Hub Return Button
        hub_hover = self.btn_hub_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, COLOR_CARD_HOVER if hub_hover else COLOR_CARD_BG, self.btn_hub_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.btn_hub_rect, width=1, border_radius=6)
        btn_text = self.status_font.render("◄ [H] Return to Hub", True, COLOR_TEXT)
        surface.blit(btn_text, btn_text.get_rect(center=self.btn_hub_rect.center))

        # Title
        lvl_title = self.title_font.render("CHAPTER 2: THE WATCHER", True, COLOR_SELECTED)
        surface.blit(lvl_title, (SCREEN_WIDTH // 2 - lvl_title.get_width() // 2, 20))
