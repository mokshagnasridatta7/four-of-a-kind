"""Unit tests for The Watcher playable level mechanics, stealth, and Kabir meeting event."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()

from game_state import (
    CHAPTER_THE_WATCHER,
    FLAG_KNOWS_KABIR_MEETING,
    GameState,
    has_flag,
)
from level_watcher import TheWatcherLevel


class TestTheWatcherLevel(unittest.TestCase):
    """Test suite for 'The Watcher' stealth observation level."""

    def setUp(self):
        self.level = TheWatcherLevel()
        self.state = GameState(current_chapter=CHAPTER_THE_WATCHER)

    def test_initial_state(self):
        """Initial state starts on Day 1 with 0% progress and no alert."""
        self.assertEqual(self.level.current_day, 1)
        self.assertEqual(self.level.total_days, 3)
        self.assertEqual(self.level.day_progress, 0.0)
        self.assertEqual(self.level.detection_level, 0.0)
        self.assertFalse(self.level.is_spotted)
        self.assertFalse(self.level.meeting_witnessed)

    def test_cover_versus_observing_position(self):
        """Player is in cover when stepped back from parapet; observing when at edge."""
        # Initial position is in cover (y = 490 >= 465)
        self.assertTrue(self.level.is_in_cover())
        self.assertFalse(self.level.is_observing())

        # Move forward to parapet edge (y = 430 < 465)
        self.level.player.rect.centery = 430
        self.assertFalse(self.level.is_in_cover())
        self.assertTrue(self.level.is_observing())

    def test_observation_zones(self):
        """Confirm the 3 distinct observation zones along the parapet."""
        self.level.player.rect.centery = 430

        # Zone 1: Main Gate & Perimeter (left)
        self.level.player.rect.centerx = 120
        self.assertEqual(self.level.get_active_zone().id_name, "gate")

        # Zone 2: Vault Exterior (center)
        self.level.player.rect.centerx = 400
        self.assertEqual(self.level.get_active_zone().id_name, "courtyard")

        # Zone 3: Back Service Alley (right)
        self.level.player.rect.centerx = 640
        self.assertEqual(self.level.get_active_zone().id_name, "alley")

    def test_spotted_resets_attempt_without_ending_chapter(self):
        """Being spotted resets current day attempt and returns player to cover without quitting."""
        self.level.current_day = 2
        self.level.day_progress = 65.0
        self.level.player.rect.centery = 430  # at the edge

        # Guard spots the player
        self.level.trigger_spotted()
        self.assertTrue(self.level.is_spotted)
        self.assertEqual(self.level.detection_level, 100.0)

        # Reset current day
        self.level.reset_current_day()
        self.assertFalse(self.level.is_spotted)
        self.assertEqual(self.level.current_day, 2)  # Still on Day 2
        self.assertEqual(self.level.day_progress, 0.0)
        self.assertTrue(self.level.is_in_cover())  # Moved safely to cover

    def test_witness_kabir_meeting_sets_flag(self):
        """Observing the Back Alley on Day 2 sets knows_kabir_meeting flag."""
        self.assertFalse(has_flag(self.state, FLAG_KNOWS_KABIR_MEETING))

        new_state = self.level.witness_kabir_meeting(self.state)

        # State immutability verified
        self.assertIsNot(self.state, new_state)
        self.assertFalse(has_flag(self.state, FLAG_KNOWS_KABIR_MEETING))
        self.assertTrue(has_flag(new_state, FLAG_KNOWS_KABIR_MEETING))
        self.assertTrue(self.level.meeting_witnessed)

    def test_completion_without_meeting_returns_to_hub(self):
        """Completing surveillance without witnessing meeting finishes chapter and returns to hub."""
        action, final_state = self.level.complete_surveillance(self.state)

        self.assertEqual(action, "return_to_hub")
        self.assertIsNone(final_state.current_chapter)
        self.assertIn(CHAPTER_THE_WATCHER, final_state.completed_chapters)
        self.assertFalse(has_flag(final_state, FLAG_KNOWS_KABIR_MEETING))

    def test_completion_with_meeting_preserves_flag(self):
        """Completing surveillance after witnessing meeting preserves flag and returns to hub."""
        # 1. Witness meeting
        state_with_meeting = self.level.witness_kabir_meeting(self.state)
        self.assertTrue(has_flag(state_with_meeting, FLAG_KNOWS_KABIR_MEETING))

        # 2. Complete surveillance
        action, final_state = self.level.complete_surveillance(state_with_meeting)

        self.assertEqual(action, "return_to_hub")
        self.assertIsNone(final_state.current_chapter)
        self.assertIn(CHAPTER_THE_WATCHER, final_state.completed_chapters)
        self.assertTrue(has_flag(final_state, FLAG_KNOWS_KABIR_MEETING))

    def test_return_to_hub_input_does_not_complete_chapter(self):
        """Pressing H or ESC exits to hub without completing the chapter."""
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)
        action, state_out = self.level.handle_event(esc_event, self.state)

        self.assertEqual(action, "return_to_hub")
        self.assertNotIn(CHAPTER_THE_WATCHER, state_out.completed_chapters)


if __name__ == "__main__":
    unittest.main()
