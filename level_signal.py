"""The Signal - Playable timed alarm disable level.

A timed puzzle where the player must disable an underground alarm system before
the countdown timer runs out.
- If 'knows_sana_contact' is set in GameState, an easier/shorter path is provided
  via a visible shortcut (Sana's Backdoor Bypass Terminal at 142.85 MHz).
- If not set, the player must solve the full harder 4-node relay sequence.
- Failing the timer triggers an alarm trip and sends the player back to the Hub
  (not an instant retry).
- Completing the puzzle calls complete_chapter(state, 'The Signal') and returns to the Hub.
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple
import math
import pygame

from game_state import (
    CHAPTER_THE_SIGNAL,
    FLAG_KNOWS_SANA_CONTACT,
    GameState,
    complete_chapter,
    has_flag,
    set_current_chapter,
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
class RelayNode:
    """An interactive alarm relay terminal in the circuit grid."""

    id_idx: int
    name: str
    label: str
    rect: pygame.Rect
    is_shortcut: bool = False
    is_active: bool = False


class TheSignalLevel:
    """Manages Chapter 3: The Signal timed alarm disabling puzzle."""

    def __init__(self):
        # Interactive player sprite
        self.all_sprites = pygame.sprite.Group()
        self.player = Player(110, 480)
        self.all_sprites.add(self.player)

        # Timed Countdown Settings (in seconds)
        self.time_limit_sec: float = 38.0
        self.time_remaining: float = self.time_limit_sec
        self.timer_failed: bool = False
        self.fail_transition_timer: float = 0.0

        # Shortcut & Path Availability
        self.shortcut_unlocked: bool = False
        self.current_step: int = 0  # Sequence step for standard path
        self.completed_nodes: List[int] = []  # Indices of activated nodes
        self.used_shortcut: bool = False

        # Completion State
        self.puzzle_completed: bool = False
        self.success_dialog_open: bool = False

        # Failure State
        self.failure_dialog_open: bool = False

        # 4 Standard Relay Terminals
        self.standard_nodes: List[RelayNode] = [
            RelayNode(
                id_idx=0,
                name="Relay 1: Power Feed",
                label="[Node 1: Main Feed]",
                rect=pygame.Rect(90, 240, 120, 75),
            ),
            RelayNode(
                id_idx=1,
                name="Relay 2: Frequency Filter",
                label="[Node 2: Filter]",
                rect=pygame.Rect(260, 360, 120, 75),
            ),
            RelayNode(
                id_idx=2,
                name="Relay 3: Wave Modulator",
                label="[Node 3: Modulator]",
                rect=pygame.Rect(430, 360, 120, 75),
            ),
            RelayNode(
                id_idx=3,
                name="Relay 4: Master Breaker",
                label="[Node 4: Master Breaker]",
                rect=pygame.Rect(600, 240, 120, 75),
            ),
        ]

        # 1 Sana's Backdoor Bypass Terminal (Visible shortcut when knows_sana_contact is True)
        self.sana_shortcut_node = RelayNode(
            id_idx=99,
            name="Sana's Backdoor Bypass",
            label="[★ Sana's Backdoor (142.85 MHz)]",
            rect=pygame.Rect(340, 200, 130, 85),
            is_shortcut=True,
        )

        # Buttons
        self.btn_hub_rect = pygame.Rect(25, 18, 140, 34)

        # Fonts
        self.title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 20, bold=True)
        self.timer_font = pygame.font.SysFont("Consolas, monospace, Segoe UI", 20, bold=True)
        self.header_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 14, bold=True)
        self.node_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.desc_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 12)
        self.prompt_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 13, bold=True)
        self.dialog_title_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 18, bold=True)
        self.dialog_body_font = pygame.font.SysFont("Segoe UI, Arial, sans-serif", 14)

        # Ambient animation timer
        self.anim_time = 0.0

    def reset(self, state: GameState):
        """Reset puzzle attempt and configure shortcut based on GameState."""
        self.time_remaining = self.time_limit_sec
        self.timer_failed = False
        self.fail_transition_timer = 0.0
        self.current_step = 0
        self.completed_nodes.clear()
        self.used_shortcut = False
        self.puzzle_completed = False
        self.success_dialog_open = False
        self.failure_dialog_open = False

        # Reset node states
        for node in self.standard_nodes:
            node.is_active = False
        self.sana_shortcut_node.is_active = False

        # Check if Sana's contact is known
        self.shortcut_unlocked = has_flag(state, FLAG_KNOWS_SANA_CONTACT)

        # Position player at starting terminal
        self.player.rect.center = (110, 480)
        self.player.pos = pygame.math.Vector2(self.player.rect.center)

    def is_shortcut_available(self, state: GameState) -> bool:
        """Return True if Sana's contact flag is set in GameState."""
        return has_flag(state, FLAG_KNOWS_SANA_CONTACT)

    def trigger_node(self, node: RelayNode, state: GameState) -> bool:
        """Attempt to activate a relay terminal. Returns True if successfully triggered."""
        if self.puzzle_completed or self.timer_failed:
            return False

        # 1. Sana's Shortcut Terminal
        if node.is_shortcut:
            if not self.shortcut_unlocked:
                return False  # Locked without Sana's contact

            # Shortcut requires Node 0 (Main Feed) to be online first
            if 0 in self.completed_nodes:
                node.is_active = True
                self.completed_nodes.append(99)
                self.used_shortcut = True
                self.puzzle_completed = True
                self.success_dialog_open = True
                return True
            return False

        # 2. Standard Relay Nodes (Must be activated in sequence 0 -> 1 -> 2 -> 3)
        if node.id_idx == self.current_step:
            node.is_active = True
            self.completed_nodes.append(node.id_idx)
            self.current_step += 1

            # If Node 3 (Master Breaker) reached, standard puzzle is complete!
            if node.id_idx == 3:
                self.puzzle_completed = True
                self.success_dialog_open = True
            return True

        return False

    def finish_chapter(self, state: GameState) -> Tuple[str, GameState]:
        """Mark 'The Signal' complete and return to the Hub."""
        new_state = complete_chapter(state, CHAPTER_THE_SIGNAL)
        new_state = set_current_chapter(new_state, None)
        return "return_to_hub", new_state

    def fail_and_return_to_hub(self, state: GameState) -> Tuple[str, GameState]:
        """Failing the timer sends player to the Hub without completing the chapter."""
        new_state = set_current_chapter(state, None)
        return "return_to_hub", new_state

    def _get_nearby_node(self) -> Optional[RelayNode]:
        """Find interactive node near player."""
        player_center = self.player.rect.center

        # Check Sana's shortcut terminal
        dist_sana = math.hypot(
            player_center[0] - self.sana_shortcut_node.rect.centerx,
            player_center[1] - self.sana_shortcut_node.rect.centery,
        )
        if dist_sana < 85:
            return self.sana_shortcut_node

        # Check standard nodes
        for node in self.standard_nodes:
            dist = math.hypot(
                player_center[0] - node.rect.centerx,
                player_center[1] - node.rect.centery,
            )
            if dist < 85:
                return node

        return None

    def handle_event(
        self, event: pygame.event.Event, state: GameState
    ) -> Tuple[Optional[str], GameState]:
        """Handle inputs, node interactions, and dialog dismissals."""
        # 1. Success Dialog -> complete chapter and return to hub
        if self.success_dialog_open:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e):
                return self.finish_chapter(state)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self.finish_chapter(state)
            return None, state

        # 2. Failure Dialog -> return to hub without instant retry
        if self.failure_dialog_open:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_e, pygame.K_ESCAPE):
                return self.fail_and_return_to_hub(state)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                return self.fail_and_return_to_hub(state)
            return None, state

        # 3. Standard In-Level Inputs
        if event.type == pygame.KEYDOWN:
            # Return to Hub
            if event.key in (pygame.K_ESCAPE, pygame.K_h):
                return "return_to_hub", state

            # Interact key [E] or SPACE
            elif event.key in (pygame.K_e, pygame.K_SPACE):
                nearby = self._get_nearby_node()
                if nearby:
                    self.trigger_node(nearby, state)
                    return None, state

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mouse_pos = event.pos

            # Return to Hub button
            if self.btn_hub_rect.collidepoint(mouse_pos):
                return "return_to_hub", state

            # Direct click on nodes
            if self.sana_shortcut_node.rect.collidepoint(mouse_pos):
                self.trigger_node(self.sana_shortcut_node, state)
                return None, state

            for node in self.standard_nodes:
                if node.rect.collidepoint(mouse_pos):
                    self.trigger_node(node, state)
                    return None, state

        return None, state

    def update(
        self, dt: float, state: GameState
    ) -> Tuple[Optional[str], Optional[GameState]]:
        """Update simulation, timer countdown, and check fail/success conditions."""
        self.anim_time += dt

        # Stop timer if dialogs are open
        if self.success_dialog_open or self.failure_dialog_open:
            return None, None

        # 1. Countdown Alarm Timer
        if not self.puzzle_completed:
            self.time_remaining -= dt
            if self.time_remaining <= 0.0:
                self.time_remaining = 0.0
                self.timer_failed = True
                self.failure_dialog_open = True
                return None, None

        # 2. Update Player Sprite & Bounds
        self.all_sprites.update(dt)
        self.player.rect.left = max(35, self.player.rect.left)
        self.player.rect.right = min(SCREEN_WIDTH - 35, self.player.rect.right)
        self.player.rect.top = max(180, self.player.rect.top)
        self.player.rect.bottom = min(SCREEN_HEIGHT - 35, self.player.rect.bottom)
        self.player.pos = pygame.math.Vector2(self.player.rect.center)

        return None, None

    def draw(self, surface: pygame.Surface, state: GameState):
        """Render telecom relay room, cables, timer HUD, and terminals."""
        surface.fill(COLOR_BACKGROUND)

        # 1. Room Floor Grid & Architecture
        self._draw_relay_room(surface)

        # 2. Cable Conduits & Power Lines
        self._draw_circuit_wires(surface)

        # 3. Relay Terminals (Standard & Shortcut)
        self._draw_terminals(surface)

        # 4. Player Sprite
        self.all_sprites.draw(surface)

        # 5. Proximity Prompts
        self._draw_proximity_prompt(surface)

        # 6. Top Timer & Path Status HUD
        self._draw_hud(surface)

        # 7. Modals / Dialogs
        if self.success_dialog_open:
            self._draw_success_dialog(surface)
        elif self.failure_dialog_open:
            self._draw_failure_dialog(surface)

    def _draw_relay_room(self, surface: pygame.Surface):
        """Draw concrete floor grid, server racks, and underground ambience."""
        # Top wall barrier
        wall_rect = pygame.Rect(25, 165, SCREEN_WIDTH - 50, 6)
        pygame.draw.rect(surface, (45, 54, 72), wall_rect, border_radius=3)

        # Ambient floor tiles
        for x in range(35, SCREEN_WIDTH - 35, 55):
            pygame.draw.line(surface, (23, 28, 38), (x, 175), (x, SCREEN_HEIGHT - 35))
        for y in range(175, SCREEN_HEIGHT - 35, 55):
            pygame.draw.line(surface, (23, 28, 38), (35, y), (SCREEN_WIDTH - 35, y))

    def _draw_circuit_wires(self, surface: pygame.Surface):
        """Render conduits connecting terminals, illuminating when active."""
        # Standard Wire 0 -> 1 -> 2 -> 3
        coords = [
            self.standard_nodes[0].rect.center,
            self.standard_nodes[1].rect.center,
            self.standard_nodes[2].rect.center,
            self.standard_nodes[3].rect.center,
        ]

        for i in range(len(coords) - 1):
            is_active_wire = (i + 1) in self.completed_nodes
            wire_col = (70, 150, 240) if is_active_wire else (40, 50, 68)
            wire_width = 3 if is_active_wire else 2
            pygame.draw.line(surface, wire_col, coords[i], coords[i + 1], wire_width)

        # Sana's Shortcut Conduit: Node 0 -> Sana Terminal -> Node 3
        sana_pt = self.sana_shortcut_node.rect.center
        pt0 = self.standard_nodes[0].rect.center
        pt3 = self.standard_nodes[3].rect.center

        # Pulse brightness for shortcut if available
        pulse = (math.sin(self.anim_time * 6.0) + 1.0) / 2.0
        if self.shortcut_unlocked:
            if 99 in self.completed_nodes:
                s_wire_col = (64, 200, 120)
                s_width = 4
            else:
                s_wire_col = (int(40 + 60 * pulse), int(180 + 40 * pulse), 220)
                s_width = 3
        else:
            s_wire_col = (38, 42, 52)
            s_width = 1

        pygame.draw.line(surface, s_wire_col, pt0, sana_pt, s_width)
        pygame.draw.line(surface, s_wire_col, sana_pt, pt3, s_width)

    def _draw_terminals(self, surface: pygame.Surface):
        """Draw interactive breaker nodes and Sana's backdoor terminal."""
        mouse_pos = pygame.mouse.get_pos()

        # 1. Standard Nodes
        for node in self.standard_nodes:
            is_next = node.id_idx == self.current_step
            is_hover = node.rect.collidepoint(mouse_pos)

            if node.is_active:
                bg_col = (25, 55, 40)
                border_col = COLOR_COMPLETED
                border_w = 2
            elif is_next:
                bg_col = COLOR_CARD_HOVER if is_hover else (35, 48, 68)
                border_col = COLOR_SELECTED
                border_w = 2
            else:
                bg_col = COLOR_CARD_BG
                border_col = COLOR_CARD_BORDER
                border_w = 1

            pygame.draw.rect(surface, bg_col, node.rect, border_radius=6)
            pygame.draw.rect(surface, border_col, node.rect, width=border_w, border_radius=6)

            # Node label
            lbl_surf = self.node_font.render(node.label, True, border_col)
            surface.blit(lbl_surf, (node.rect.x + 8, node.rect.y + 10))

            status_str = "✓ BYPASSED" if node.is_active else ("◄ NEXT TARGET" if is_next else "LOCKED")
            status_col = COLOR_COMPLETED if node.is_active else (COLOR_SELECTED if is_next else COLOR_MUTED)
            st_surf = self.desc_font.render(status_str, True, status_col)
            surface.blit(st_surf, (node.rect.x + 8, node.rect.y + 36))

        # 2. Sana's Backdoor Bypass Terminal (Visible shortcut)
        s_rect = self.sana_shortcut_node.rect
        s_hover = s_rect.collidepoint(mouse_pos)
        is_s_done = self.sana_shortcut_node.is_active

        if self.shortcut_unlocked:
            if is_s_done:
                s_bg = (25, 55, 40)
                s_border = COLOR_COMPLETED
            else:
                s_bg = (30, 52, 65) if s_hover else (24, 42, 54)
                s_border = (80, 210, 240)
            s_width = 2
        else:
            s_bg = (24, 28, 36)
            s_border = (50, 55, 68)
            s_width = 1

        pygame.draw.rect(surface, s_bg, s_rect, border_radius=8)
        pygame.draw.rect(surface, s_border, s_rect, width=s_width, border_radius=8)

        # Shortcut Header
        if self.shortcut_unlocked:
            s_title = self.node_font.render("★ SANA'S BYPASS", True, (80, 210, 240))
            s_sub = self.desc_font.render("142.85 MHz Secure Link", True, COLOR_TEXT)
            s_hint = "✓ BYPASS LINKED" if is_s_done else "SHORTCUT UNLOCKED"
            s_hint_col = COLOR_COMPLETED if is_s_done else (100, 220, 255)
        else:
            s_title = self.node_font.render("LOCKED TERMINAL", True, COLOR_MUTED)
            s_sub = self.desc_font.render("Sana's Frequency Req.", True, (110, 120, 135))
            s_hint = "Missing Comms Key"
            s_hint_col = (110, 120, 135)

        surface.blit(s_title, (s_rect.x + 10, s_rect.y + 10))
        surface.blit(s_sub, (s_rect.x + 10, s_rect.y + 32))
        h_surf = self.desc_font.render(s_hint, True, s_hint_col)
        surface.blit(h_surf, (s_rect.x + 10, s_rect.y + 54))

    def _draw_proximity_prompt(self, surface: pygame.Surface):
        """Floating interaction prompt when player approaches a terminal."""
        nearby = self._get_nearby_node()
        if not nearby:
            return

        midtop = self.player.rect.midtop
        if nearby.is_shortcut:
            if not self.shortcut_unlocked:
                text = "Terminal Locked: Requires Sana's Contact Frequency"
                col = (150, 160, 175)
            elif 0 not in self.completed_nodes:
                text = "Bypass Node 1 First to establish feed for Sana"
                col = (240, 180, 50)
            elif nearby.is_active:
                text = "✓ Sana's Backdoor Active"
                col = COLOR_COMPLETED
            else:
                text = "[E / Click] Upload Sana's 142.85 MHz Bypass Cipher!"
                col = (80, 210, 240)
        else:
            if nearby.is_active:
                text = f"✓ {nearby.name} Already Bypassed"
                col = COLOR_COMPLETED
            elif nearby.id_idx == self.current_step:
                text = f"[E / Click] Bypass {nearby.name}"
                col = COLOR_COMPLETED
            else:
                text = f"Bypass previous relay nodes first ({self.current_step + 1}/{len(self.standard_nodes)})"
                col = (240, 180, 50)

        p_surf = self.prompt_font.render(text, True, col)
        p_rect = p_surf.get_rect(midbottom=(midtop[0], midtop[1] - 10))
        bg = p_rect.inflate(12, 6)
        pygame.draw.rect(surface, (20, 24, 34), bg, border_radius=4)
        pygame.draw.rect(surface, col, bg, width=1, border_radius=4)
        surface.blit(p_surf, p_rect)

    def _draw_hud(self, surface: pygame.Surface):
        """Render top countdown clock, path route status, and exit button."""
        mouse_pos = pygame.mouse.get_pos()

        # Top Return to Hub Button
        hub_hover = self.btn_hub_rect.collidepoint(mouse_pos)
        pygame.draw.rect(surface, COLOR_CARD_HOVER if hub_hover else COLOR_CARD_BG, self.btn_hub_rect, border_radius=6)
        pygame.draw.rect(surface, COLOR_CARD_BORDER, self.btn_hub_rect, width=1, border_radius=6)
        btn_text = self.desc_font.render("◄ [H] Return to Hub", True, COLOR_TEXT)
        surface.blit(btn_text, btn_text.get_rect(center=self.btn_hub_rect.center))

        # Level Title
        lvl_title = self.title_font.render("CHAPTER 3: THE SIGNAL", True, COLOR_SELECTED)
        surface.blit(lvl_title, (SCREEN_WIDTH // 2 - lvl_title.get_width() // 2, 18))

        # Countdown Timer Box (Top Center-Right)
        timer_box = pygame.Rect(SCREEN_WIDTH - 280, 14, 255, 42)
        pygame.draw.rect(surface, (25, 32, 44), timer_box, border_radius=6)

        # Flashing red when under 10 seconds
        if self.time_remaining < 10.0:
            flash_col = (255, 60, 60) if int(self.anim_time * 4) % 2 == 0 else (200, 40, 40)
        elif self.time_remaining < 20.0:
            flash_col = (240, 170, 40)
        else:
            flash_col = COLOR_COMPLETED

        pygame.draw.rect(surface, flash_col, timer_box, width=1, border_radius=6)

        time_str = f"ALARM TIMER: {self.time_remaining:04.1f}s"
        t_surf = self.timer_font.render(time_str, True, flash_col)
        surface.blit(t_surf, t_surf.get_rect(center=timer_box.center))

        # Bottom Route Hint Banner
        hint_bar = pygame.Rect(35, 75, SCREEN_WIDTH - 70, 36)
        pygame.draw.rect(surface, (24, 30, 42), hint_bar, border_radius=6)
        pygame.draw.rect(surface, (45, 55, 75), hint_bar, width=1, border_radius=6)

        if self.shortcut_unlocked:
            path_info = "★ SANA'S SHORTCUT ACTIVE: Bypass Node 1, then access Backdoor Terminal (2 steps)"
            path_col = (80, 210, 240)
        else:
            path_info = "FULL RELAY REQUIRED: Bypass all 4 nodes in sequence (Node 1 -> 2 -> 3 -> 4)"
            path_col = COLOR_MUTED

        info_surf = self.header_font.render(path_info, True, path_col)
        surface.blit(info_surf, (hint_bar.x + 15, hint_bar.y + 9))

    def _draw_success_dialog(self, surface: pygame.Surface):
        """Dialogue on successfully disabling the alarm."""
        diag_w, diag_h = 580, 260
        diag = pygame.Rect((SCREEN_WIDTH - diag_w) // 2, (SCREEN_HEIGHT - diag_h) // 2, diag_w, diag_h)

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 180))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (20, 34, 28), diag, border_radius=10)
        pygame.draw.rect(surface, COLOR_COMPLETED, diag, width=2, border_radius=10)

        title = self.dialog_title_font.render("★ ALARM SUBSYSTEM OFFLINE ★", True, COLOR_COMPLETED)
        surface.blit(title, title.get_rect(center=(diag.centerx, diag.y + 28)))

        route_taken = "Sana's Backdoor Bypass (Shortcut)" if self.used_shortcut else "Full 4-Node Breaker Sequence"
        lines = [
            f"• Route Used:       {route_taken}",
            f"• Time Remaining:   {self.time_remaining:04.1f} seconds",
            "",
            "The underground security alarm has been neutralized.",
            "Sana confirms the green light over the radio comms.",
            "The crew has a clear window for Chapter 4: The Job.",
        ]
        curr_y = diag.y + 64
        for line in lines:
            col = (80, 210, 240) if "Sana's" in line else COLOR_TEXT
            surf = self.dialog_body_font.render(line, True, col)
            surface.blit(surf, (diag.x + 35, curr_y))
            curr_y += 22

        btn_surf = self.prompt_font.render("Press SPACE / Click to Complete Chapter & Return to Hub", True, COLOR_COMPLETED)
        surface.blit(btn_surf, btn_surf.get_rect(center=(diag.centerx, diag.bottom - 24)))

    def _draw_failure_dialog(self, surface: pygame.Surface):
        """Dialogue on countdown timer failure (sends player to Hub)."""
        diag_w, diag_h = 580, 240
        diag = pygame.Rect((SCREEN_WIDTH - diag_w) // 2, (SCREEN_HEIGHT - diag_h) // 2, diag_w, diag_h)

        dim = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 190))
        surface.blit(dim, (0, 0))

        pygame.draw.rect(surface, (36, 16, 16), diag, border_radius=10)
        pygame.draw.rect(surface, (240, 60, 60), diag, width=2, border_radius=10)

        title = self.dialog_title_font.render("! ALARM TRIPPED — TIMER EXPIRED !", True, (255, 80, 80))
        surface.blit(title, title.get_rect(center=(diag.centerx, diag.y + 28)))

        lines = [
            "The countdown timer ran out before the alarm could be disabled.",
            "Security dispatchers were alerted and the perimeter locked down.",
            "",
            "You were forced to evacuate the telecom station.",
            "Returning to the Chapter Hub (re-enter from Hub to retry).",
        ]
        curr_y = diag.y + 68
        for line in lines:
            col = (255, 140, 140) if "evacuate" in line else COLOR_TEXT
            surf = self.dialog_body_font.render(line, True, col)
            surface.blit(surf, (diag.x + 35, curr_y))
            curr_y += 22

        btn_surf = self.prompt_font.render("Press SPACE / Click to Exit to Hub", True, (255, 100, 100))
        surface.blit(btn_surf, btn_surf.get_rect(center=(diag.centerx, diag.bottom - 24)))
