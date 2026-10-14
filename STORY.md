"""Unit tests for the immutable GameState and its pure transition functions."""

import unittest
from dataclasses import FrozenInstanceError

from game_state import (
    FLAG_ACCUSED_KABIR,
    FLAG_FOUND_FALLOUT_EVIDENCE,
    FLAG_KNOWS_CALL_CONTENT,
    FLAG_KNOWS_KABIR_MEETING,
    FLAG_KNOWS_SANA_CONTACT,
    GameState,
    complete_chapter,
    has_flag,
    set_current_chapter,
    set_flag,
)


class TestGameStateImmutability(unittest.TestCase):
    """Verify that GameState instances cannot be mutated directly or indirectly."""

    def test_default_values(self):
        state = GameState()
        self.assertEqual(state.flags, frozenset())
        self.assertEqual(state.completed_chapters, frozenset())
        self.assertIsNone(state.current_chapter)

    def test_frozen_dataclass_prevents_attribute_reassignment(self):
        state = GameState()
        with self.assertRaises(FrozenInstanceError):
            state.current_chapter = "chapter_1"  # type: ignore

        with self.assertRaises(FrozenInstanceError):
            state.flags = frozenset({"test"})  # type: ignore

        with self.assertRaises(FrozenInstanceError):
            state.completed_chapters = frozenset({"ch1"})  # type: ignore

    def test_collection_immutability(self):
        state = GameState()
        # frozenset does not have an .add() or .remove() method
        self.assertFalse(hasattr(state.flags, "add"))
        self.assertFalse(hasattr(state.completed_chapters, "add"))

    def test_mutable_sets_converted_to_frozenset(self):
        mutable_flags = {"test_flag"}
        mutable_chapters = {"prologue"}
        state = GameState(flags=mutable_flags, completed_chapters=mutable_chapters)

        self.assertIsInstance(state.flags, frozenset)
        self.assertIsInstance(state.completed_chapters, frozenset)

        # Mutating the original external set must not affect state
        mutable_flags.add("injected_flag")
        mutable_chapters.add("injected_chapter")
        self.assertNotIn("injected_flag", state.flags)
        self.assertNotIn("injected_chapter", state.completed_chapters)


class TestPureFunctions(unittest.TestCase):
    """Verify that state transition functions are pure and never mutate inputs."""

    def test_set_flag_does_not_mutate_original_state(self):
        original = GameState(flags=frozenset({"initial_flag"}))
        new_state = set_flag(original, "new_flag")

        # Must be distinct instances
        self.assertIsNot(original, new_state)

        # Original state remains strictly untouched
        self.assertEqual(original.flags, frozenset({"initial_flag"}))
        self.assertNotIn("new_flag", original.flags)

        # New state contains the added flag alongside previous flags
        self.assertEqual(new_state.flags, frozenset({"initial_flag", "new_flag"}))
        self.assertIn("new_flag", new_state.flags)

    def test_has_flag(self):
        state = GameState(flags=frozenset({FLAG_KNOWS_SANA_CONTACT}))
        self.assertTrue(has_flag(state, FLAG_KNOWS_SANA_CONTACT))
        self.assertFalse(has_flag(state, FLAG_KNOWS_KABIR_MEETING))

        # has_flag must not alter state
        self.assertEqual(state.flags, frozenset({FLAG_KNOWS_SANA_CONTACT}))

    def test_complete_chapter_does_not_mutate_original_state(self):
        original = GameState(
            completed_chapters=frozenset({"intro"}),
            current_chapter="chapter_1",
        )
        new_state = complete_chapter(original, "chapter_1")

        # Must be distinct instances
        self.assertIsNot(original, new_state)

        # Original state remains strictly untouched
        self.assertEqual(original.completed_chapters, frozenset({"intro"}))
        self.assertEqual(original.current_chapter, "chapter_1")

        # New state contains the new chapter
        self.assertEqual(
            new_state.completed_chapters, frozenset({"intro", "chapter_1"})
        )
        self.assertIn("chapter_1", new_state.completed_chapters)

    def test_set_current_chapter_does_not_mutate_original_state(self):
        original = GameState(current_chapter=None)
        new_state = set_current_chapter(original, "chapter_2")

        self.assertIsNot(original, new_state)
        self.assertIsNone(original.current_chapter)
        self.assertEqual(new_state.current_chapter, "chapter_2")

        # Returning to hub
        hub_state = set_current_chapter(new_state, None)
        self.assertIsNot(new_state, hub_state)
        self.assertEqual(new_state.current_chapter, "chapter_2")
        self.assertIsNone(hub_state.current_chapter)

    def test_story_flags_workflow(self):
        """Test the specified narrative flags in a sequential chain."""
        story_flags = [
            FLAG_KNOWS_SANA_CONTACT,
            FLAG_KNOWS_KABIR_MEETING,
            FLAG_KNOWS_CALL_CONTENT,
            FLAG_ACCUSED_KABIR,
            FLAG_FOUND_FALLOUT_EVIDENCE,
        ]

        states = [GameState()]

        for flag in story_flags:
            previous = states[-1]
            next_state = set_flag(previous, flag)
            states.append(next_state)

        # Verify that all intermediate states preserved their exact flag sets
        for i, state in enumerate(states):
            self.assertEqual(len(state.flags), i)
            for j in range(i):
                self.assertTrue(has_flag(state, story_flags[j]))
            for k in range(i, len(story_flags)):
                self.assertFalse(has_flag(state, story_flags[k]))

    def test_independent_branches(self):
        """Branching from the same state creates independent timelines."""
        base_state = GameState()

        timeline_a = set_flag(base_state, FLAG_ACCUSED_KABIR)
        timeline_b = set_flag(base_state, FLAG_FOUND_FALLOUT_EVIDENCE)

        self.assertEqual(base_state.flags, frozenset())
        self.assertEqual(timeline_a.flags, frozenset({FLAG_ACCUSED_KABIR}))
        self.assertEqual(timeline_b.flags, frozenset({FLAG_FOUND_FALLOUT_EVIDENCE}))
        self.assertFalse(has_flag(timeline_a, FLAG_FOUND_FALLOUT_EVIDENCE))
        self.assertFalse(has_flag(timeline_b, FLAG_ACCUSED_KABIR))


if __name__ == "__main__":
    unittest.main()
