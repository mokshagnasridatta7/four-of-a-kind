"""Game state module.

Provides an immutable GameState data structure and pure functions to update state
without ever mutating previous instances.
"""

from dataclasses import dataclass, field, replace
from typing import FrozenSet, Iterable, Optional, Set

# Known story flags
FLAG_KNOWS_SANA_CONTACT = "knows_sana_contact"
FLAG_KNOWS_KABIR_MEETING = "knows_kabir_meeting"
FLAG_KNOWS_CALL_CONTENT = "knows_call_content"
FLAG_ACCUSED_KABIR = "accused_kabir"
FLAG_FOUND_FALLOUT_EVIDENCE = "found_fallout_evidence"

ALL_STORY_FLAGS = frozenset(
    {
        FLAG_KNOWS_SANA_CONTACT,
        FLAG_KNOWS_KABIR_MEETING,
        FLAG_KNOWS_CALL_CONTENT,
        FLAG_ACCUSED_KABIR,
        FLAG_FOUND_FALLOUT_EVIDENCE,
    }
)

# 7 Core Chapters
CHAPTER_THE_PLAN = "The Plan"
CHAPTER_THE_WATCHER = "The Watcher"
CHAPTER_THE_SIGNAL = "The Signal"
CHAPTER_THE_JOB = "The Job"
CHAPTER_THE_GETAWAY = "The Getaway"
CHAPTER_THE_SPLIT = "The Split"
CHAPTER_THE_FALLOUT = "The Fallout"

CHAPTERS = (
    CHAPTER_THE_PLAN,
    CHAPTER_THE_WATCHER,
    CHAPTER_THE_SIGNAL,
    CHAPTER_THE_JOB,
    CHAPTER_THE_GETAWAY,
    CHAPTER_THE_SPLIT,
    CHAPTER_THE_FALLOUT,
)

FINALE_CHAPTER = "Finale"


@dataclass(frozen=True)
class GameState:
    """Immutable representation of the narrative and progression game state.

    Attributes:
        flags: A frozenset of flag strings indicating player knowledge and choices.
        completed_chapters: A frozenset of chapter names that have been finished.
        current_chapter: The name of the active chapter, or None if the player is at the hub.
    """

    flags: frozenset[str] = field(default_factory=frozenset)
    completed_chapters: frozenset[str] = field(default_factory=frozenset)
    current_chapter: Optional[str] = None

    def __post_init__(self):
        # Ensure deep immutability by converting any passed set/iterable to frozenset
        if not isinstance(self.flags, frozenset):
            object.__setattr__(self, "flags", frozenset(self.flags))
        if not isinstance(self.completed_chapters, frozenset):
            object.__setattr__(
                self, "completed_chapters", frozenset(self.completed_chapters)
            )


# ---------------------------------------------------------------------------
# Pure State Manipulation Functions
# ---------------------------------------------------------------------------


def set_flag(state: GameState, flag_name: str) -> GameState:
    """Return a new GameState with flag_name added to flags.

    Never mutates the input state.
    """
    new_flags = state.flags | {flag_name}
    return replace(state, flags=new_flags)


def complete_chapter(state: GameState, chapter_name: str) -> GameState:
    """Return a new GameState with chapter_name added to completed_chapters.

    Never mutates the input state.
    """
    new_completed = state.completed_chapters | {chapter_name}
    return replace(state, completed_chapters=new_completed)


def has_flag(state: GameState, flag_name: str) -> bool:
    """Check whether a given flag is present in the game state.

    Does not modify state.
    """
    return flag_name in state.flags


def set_current_chapter(state: GameState, chapter_name: Optional[str]) -> GameState:
    """Return a new GameState with the current chapter set (or None for hub).

    Never mutates the input state.
    """
    return replace(state, current_chapter=chapter_name)


def is_finale_unlocked(state: GameState) -> bool:
    """Return True if all 7 core chapters are present in completed_chapters.

    Does not modify state.
    """
    return frozenset(CHAPTERS).issubset(state.completed_chapters)


def get_available_chapters(state: GameState) -> list[str]:
    """Return the list of selectable chapter titles for the hub screen.

    'Finale' appears only once all 7 core chapters are completed.
    Does not modify state.
    """
    chapters = list(CHAPTERS)
    if is_finale_unlocked(state):
        chapters.append(FINALE_CHAPTER)
    return chapters
