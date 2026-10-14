"""Unit tests for The Plan playable level puzzle and secret mechanics."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()

from game_state import (
    CHAPTER_THE_PLAN,
    FLAG_KNOWS_SANA_CONTACT,
    GameState,
    has_flag,
    set_current_chapter,
)
from level_plan import (
    ROUTE_CHOICES,
    TIMING_CHOICES,
    TOOL_CHOICES,
    ThePlanLevel,
)


class TestThePlanLevel(unittest.TestCase):
    """Test suite for 'The Plan' level puzzle and secrets."""

    def setUp(self):
        self.level = ThePlanLevel()
        self.state = GameState(current_chapter=CHAPTER_THE_PLAN)

    def test_puzzle_options_structure(self):
        """Confirm exactly 3 choices for Route, Timing, and Tool."""
        self.assertEqual(len(ROUTE_CHOICES), 3)
        self.assertEqual(len(TIMING_CHOICES), 3)
        self.assertEqual(len(TOOL_CHOICES), 3)

    def test_plan_incomplete_initially(self):
        """Initial state has no selections and is_plan_complete is False."""
        self.assertIsNone(self.level.selected_route_idx)
        self.assertIsNone(self.level.selected_timing_idx)
        self.assertIsNone(self.level.selected_tool_idx)
        self.assertFalse(self.level.is_plan_complete())

    def test_partial_selections_remain_incomplete(self):
        """Selecting only 1 or 2 options leaves the plan incomplete."""
        self.level.select_option("route", 0)
        self.assertFalse(self.level.is_plan_complete())

        self.level.select_option("timing", 1)
        self.assertFalse(self.level.is_plan_complete())

        self.level.select_option("tool", 2)
        self.assertTrue(self.level.is_plan_complete())

    def test_investigate_secret_sets_sana_flag(self):
        """Investigating the hidden radio detail sets knows_sana_contact."""
        self.assertFalse(has_flag(self.state, FLAG_KNOWS_SANA_CONTACT))

        new_state = self.level.investigate_secret(self.state)

        # State immutability verified
        self.assertIsNot(self.state, new_state)
        self.assertFalse(has_flag(self.state, FLAG_KNOWS_SANA_CONTACT))
        self.assertTrue(has_flag(new_state, FLAG_KNOWS_SANA_CONTACT))
        self.assertTrue(self.level.secret_investigated)

    def test_puzzle_completion_without_secret(self):
        """Completing puzzle without finding secret completes chapter and returns to hub."""
        self.level.select_option("route", 1)
        self.level.select_option("timing", 0)
        self.level.select_option("tool", 1)
        self.assertTrue(self.level.is_plan_complete())

        action, final_state = self.level.execute_plan(self.state)

        self.assertEqual(action, "return_to_hub")
        self.assertIsNone(final_state.current_chapter)
        self.assertIn(CHAPTER_THE_PLAN, final_state.completed_chapters)
        self.assertFalse(has_flag(final_state, FLAG_KNOWS_SANA_CONTACT))

    def test_puzzle_completion_with_secret(self):
        """Completing puzzle after finding secret preserves flag and returns to hub."""
        # 1. Player discovers hidden secret
        state_with_flag = self.level.investigate_secret(self.state)
        self.assertTrue(has_flag(state_with_flag, FLAG_KNOWS_SANA_CONTACT))

        # 2. Player completes puzzle
        self.level.select_option("route", 2)
        self.level.select_option("timing", 2)
        self.level.select_option("tool", 0)
        self.assertTrue(self.level.is_plan_complete())

        action, final_state = self.level.execute_plan(state_with_flag)

        self.assertEqual(action, "return_to_hub")
        self.assertIsNone(final_state.current_chapter)
        self.assertIn(CHAPTER_THE_PLAN, final_state.completed_chapters)
        self.assertTrue(has_flag(final_state, FLAG_KNOWS_SANA_CONTACT))

    def test_return_to_hub_input_does_not_complete_chapter(self):
        """Pressing H or ESC exits to hub without completing the chapter."""
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)
        action, state_out = self.level.handle_event(esc_event, self.state)

        self.assertEqual(action, "return_to_hub")
        self.assertNotIn(CHAPTER_THE_PLAN, state_out.completed_chapters)

    def test_secret_interaction_via_event_when_nearby(self):
        """Pressing [E] when player is near secret triggers investigation."""
        # Move player directly onto the secret object
        self.level.player.rect.center = self.level.secret_rect.center
        self.assertTrue(self.level._is_near_secret())

        e_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
        action, new_state = self.level.handle_event(e_event, self.state)

        self.assertIsNone(action)
        self.assertTrue(has_flag(new_state, FLAG_KNOWS_SANA_CONTACT))


if __name__ == "__main__":
    unittest.main()
