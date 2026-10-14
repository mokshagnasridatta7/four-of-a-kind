"""Unit tests for The Signal timed alarm disabling puzzle and Sana shortcut mechanics."""

import os
import unittest

os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()

from game_state import (
    CHAPTER_THE_SIGNAL,
    FLAG_KNOWS_SANA_CONTACT,
    GameState,
    set_flag,
)
from level_signal import TheSignalLevel


class TestTheSignalLevel(unittest.TestCase):
    """Test suite for 'The Signal' timed puzzle, shortcut branching, and failure conditions."""

    def setUp(self):
        self.level = TheSignalLevel()
        self.state_without_sana = GameState(current_chapter=CHAPTER_THE_SIGNAL)
        self.state_with_sana = set_flag(self.state_without_sana, FLAG_KNOWS_SANA_CONTACT)

    def test_shortcut_locked_without_sana_flag(self):
        """When knows_sana_contact is absent, the shortcut remains locked."""
        self.level.reset(self.state_without_sana)
        self.assertFalse(self.level.shortcut_unlocked)
        self.assertFalse(self.level.is_shortcut_available(self.state_without_sana))

        # Attempting to trigger shortcut node fails
        success = self.level.trigger_node(self.level.sana_shortcut_node, self.state_without_sana)
        self.assertFalse(success)
        self.assertFalse(self.level.sana_shortcut_node.is_active)

    def test_shortcut_unlocked_with_sana_flag(self):
        """When knows_sana_contact is present, Sana's shortcut is available and unlocked."""
        self.level.reset(self.state_with_sana)
        self.assertTrue(self.level.shortcut_unlocked)
        self.assertTrue(self.level.is_shortcut_available(self.state_with_sana))

    def test_easier_shorter_shortcut_completion(self):
        """Sana's shortcut provides a 2-step bypass (Node 0 -> Backdoor Terminal)."""
        self.level.reset(self.state_with_sana)

        # Step 1: Activate Node 0 (Main Feed)
        node0 = self.level.standard_nodes[0]
        self.assertTrue(self.level.trigger_node(node0, self.state_with_sana))
        self.assertFalse(self.level.puzzle_completed)

        # Step 2: Activate Sana's Backdoor Shortcut
        self.assertTrue(self.level.trigger_node(self.level.sana_shortcut_node, self.state_with_sana))
        self.assertTrue(self.level.puzzle_completed)
        self.assertTrue(self.level.used_shortcut)

        # Complete chapter and verify transition to hub
        action, final_state = self.level.finish_chapter(self.state_with_sana)
        self.assertEqual(action, "return_to_hub")
        self.assertIsNone(final_state.current_chapter)
        self.assertIn(CHAPTER_THE_SIGNAL, final_state.completed_chapters)

    def test_harder_full_path_completion_without_shortcut(self):
        """Without shortcut, player must solve the full 4-node sequential path (0->1->2->3)."""
        self.level.reset(self.state_without_sana)

        # Cannot skip ahead to Node 2 or Node 3
        self.assertFalse(self.level.trigger_node(self.level.standard_nodes[2], self.state_without_sana))

        # Activate sequentially
        for i in range(4):
            node = self.level.standard_nodes[i]
            self.assertTrue(self.level.trigger_node(node, self.state_without_sana))

        self.assertTrue(self.level.puzzle_completed)
        self.assertFalse(self.level.used_shortcut)

        # Complete chapter and verify transition to hub
        action, final_state = self.level.finish_chapter(self.state_without_sana)
        self.assertEqual(action, "return_to_hub")
        self.assertIsNone(final_state.current_chapter)
        self.assertIn(CHAPTER_THE_SIGNAL, final_state.completed_chapters)

    def test_failing_timer_sends_player_to_hub(self):
        """Failing the timer sends the player to the hub without completing the chapter."""
        self.level.reset(self.state_without_sana)

        # Simulate timer running down to 0
        self.level.time_remaining = 0.5
        self.level.update(0.6, self.state_without_sana)

        self.assertTrue(self.level.timer_failed)
        self.assertTrue(self.level.failure_dialog_open)

        # Dismissing failure returns to hub without completing
        action, final_state = self.level.fail_and_return_to_hub(self.state_without_sana)
        self.assertEqual(action, "return_to_hub")
        self.assertIsNone(final_state.current_chapter)
        self.assertNotIn(CHAPTER_THE_SIGNAL, final_state.completed_chapters)

    def test_return_to_hub_input_does_not_complete_chapter(self):
        """Pressing H or ESC exits to hub cleanly without marking chapter complete."""
        self.level.reset(self.state_without_sana)
        esc_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_h)
        action, state_out = self.level.handle_event(esc_event, self.state_without_sana)

        self.assertEqual(action, "return_to_hub")
        self.assertNotIn(CHAPTER_THE_SIGNAL, state_out.completed_chapters)


if __name__ == "__main__":
    unittest.main()
