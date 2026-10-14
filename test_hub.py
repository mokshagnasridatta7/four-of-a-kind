"""Unit tests for the Chapter Hub screen logic, chapter lists, and Finale unlocking."""

import os
import unittest

# Configure headless SDL driver for environments without a display server
os.environ["SDL_VIDEODRIVER"] = "dummy"
import pygame
pygame.init()

from game_state import (
    CHAPTERS,
    FINALE_CHAPTER,
    GameState,
    complete_chapter,
    get_available_chapters,
    is_finale_unlocked,
    set_current_chapter,
)
from hub import HubScreen


class TestHubLogic(unittest.TestCase):
    """Verify chapter definitions and Finale unlocking rules."""

    def setUp(self):
        self.expected_7_chapters = (
            "The Plan",
            "The Watcher",
            "The Signal",
            "The Job",
            "The Getaway",
            "The Split",
            "The Fallout",
        )

    def test_chapter_list_definitions(self):
        """Confirm exactly 7 specific chapters in order."""
        self.assertEqual(len(CHAPTERS), 7)
        self.assertEqual(CHAPTERS, self.expected_7_chapters)
        self.assertEqual(FINALE_CHAPTER, "Finale")

    def test_finale_locked_initially(self):
        """Initially, no chapters are complete and Finale must be locked."""
        state = GameState()
        self.assertFalse(is_finale_unlocked(state))
        self.assertEqual(get_available_chapters(state), list(self.expected_7_chapters))
        self.assertNotIn(FINALE_CHAPTER, get_available_chapters(state))

    def test_finale_locked_with_partial_completion(self):
        """Finale must remain locked when 1 to 6 chapters are completed."""
        state = GameState()
        for i in range(6):
            state = complete_chapter(state, self.expected_7_chapters[i])
            self.assertFalse(
                is_finale_unlocked(state),
                f"Finale should still be locked with only {i + 1} chapters completed.",
            )
            available = get_available_chapters(state)
            self.assertEqual(len(available), 7)
            self.assertNotIn(FINALE_CHAPTER, available)

    def test_finale_unlocks_when_all_7_completed(self):
        """Finale option appears ONLY when all 7 chapters are in completed_chapters."""
        state = GameState()
        for chapter in self.expected_7_chapters:
            state = complete_chapter(state, chapter)

        self.assertTrue(is_finale_unlocked(state))
        available = get_available_chapters(state)
        self.assertEqual(len(available), 8)
        self.assertIn(FINALE_CHAPTER, available)
        self.assertEqual(available[-1], FINALE_CHAPTER)

    def test_chapter_transition_into_chapter(self):
        """Selecting any chapter transitions current_chapter into it."""
        state = GameState()
        self.assertIsNone(state.current_chapter)

        # Transition into 'The Watcher'
        active_state = set_current_chapter(state, "The Watcher")
        self.assertEqual(active_state.current_chapter, "The Watcher")

        # Transition back to Hub
        hub_state = set_current_chapter(active_state, None)
        self.assertIsNone(hub_state.current_chapter)

    def test_transition_into_finale(self):
        """Finale can be transitioned into once unlocked."""
        state = GameState()
        for chapter in self.expected_7_chapters:
            state = complete_chapter(state, chapter)

        finale_state = set_current_chapter(state, FINALE_CHAPTER)
        self.assertEqual(finale_state.current_chapter, "Finale")


class TestHubScreenInput(unittest.TestCase):
    """Verify keyboard and mouse interaction on the HubScreen."""

    def setUp(self):
        self.hub = HubScreen()
        self.state = GameState()

    def test_keyboard_navigation_wrapping(self):
        """Up and Down arrow keys navigate and wrap selection index."""
        # Initial index is 0 ("The Plan")
        self.assertEqual(self.hub.selected_index, 0)

        # Down arrow moves to index 1 ("The Watcher")
        down_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_DOWN)
        result = self.hub.handle_event(down_event, self.state)
        self.assertIsNone(result)
        self.assertEqual(self.hub.selected_index, 1)

        # Up arrow wraps back to index 0
        up_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_UP)
        result = self.hub.handle_event(up_event, self.state)
        self.assertIsNone(result)
        self.assertEqual(self.hub.selected_index, 0)

        # Up arrow from 0 wraps around to the last item (index 6, "The Fallout")
        result = self.hub.handle_event(up_event, self.state)
        self.assertIsNone(result)
        self.assertEqual(self.hub.selected_index, 6)

    def test_enter_key_selects_chapter(self):
        """Pressing Return/Enter confirms selection and returns chapter name."""
        self.hub.selected_index = 3  # "The Job"
        enter_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
        selected = self.hub.handle_event(enter_event, self.state)
        self.assertEqual(selected, "The Job")

    def test_number_key_shortcuts(self):
        """Pressing number keys 1-7 directly selects that chapter."""
        # Key '1' -> "The Plan"
        k1_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1)
        self.assertEqual(self.hub.handle_event(k1_event, self.state), "The Plan")

        # Key '5' -> "The Getaway"
        k5_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_5)
        self.assertEqual(self.hub.handle_event(k5_event, self.state), "The Getaway")

    def test_number_key_8_for_finale_when_unlocked(self):
        """Key '8' triggers Finale only when unlocked."""
        # When locked, '8' should not select anything
        k8_event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_8)
        self.assertIsNone(self.hub.handle_event(k8_event, self.state))

        # Unlock all 7
        for ch in CHAPTERS:
            self.state = complete_chapter(self.state, ch)

        # Now '8' selects Finale
        self.assertEqual(self.hub.handle_event(k8_event, self.state), FINALE_CHAPTER)

    def test_mouse_click_selection(self):
        """Simulate mouse click selecting an item from the drawn cards."""
        dummy_surface = pygame.Surface((800, 600))
        self.hub.draw(dummy_surface, self.state)

        # Item rects should be populated (7 items)
        self.assertEqual(len(self.hub.item_rects), 7)

        # Target 2nd card ("The Watcher")
        chapter_name, card_rect = self.hub.item_rects[1]
        self.assertEqual(chapter_name, "The Watcher")

        # Click inside this rect
        click_event = pygame.event.Event(
            pygame.MOUSEBUTTONDOWN, button=1, pos=card_rect.center
        )
        selected = self.hub.handle_event(click_event, self.state)
        self.assertEqual(selected, "The Watcher")


if __name__ == "__main__":
    unittest.main()
