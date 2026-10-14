# Four of a Kind — Project Progress

## 1. Project Overview
A narrative-driven 2D heist game built in Pygame using an immutable, pure state architecture. The story follows a 4-person heist crew unraveling betrayal across 7 non-linear chapters leading to an unlocked Finale.

---

## 2. Completed Milestones (Do Not Redo or Overwrite)

### [COMPLETE] Phase 1: Core Engine & Player Mechanics
- **Display & Main Loop**: Capped 60 FPS loop with decoupled event handling, logic updates, and rendering.
- **Delta-Time Physics**: Smooth, framerate-independent player movement via `dt = clock.tick(FPS) / 1000.0`.
- **Vector Input**: Normalized diagonal movement prevents the $1.41\times$ diagonal speed bug.
- **Screen Boundary Clamping**: Robust collision prevention keeping the sprite inside the viewport.
- **Dual Controls**: Simultaneous support for WASD and Arrow Keys.

### [COMPLETE] Phase 2: Central Immutable GameState
- **Data Structure (`game_state.py`)**: `GameState` implemented as a frozen dataclass ensuring full immutability.
- **Pure State Transitions**:
  - `set_flag(state, flag_name) -> GameState`: Returns new state with flag added to `flags`.
  - `complete_chapter(state, chapter_name) -> GameState`: Returns new state with chapter added to `completed_chapters`.
  - `has_flag(state, flag_name) -> bool`: Checks flag membership without modifying state.
  - `set_current_chapter(state, chapter_name) -> GameState`: Switches between active chapter and Hub (`None`).
  - `is_finale_unlocked(state) -> bool`: Pure helper checking if all 7 standard chapters are completed.
  - `get_available_chapters(state) -> list[str]`: Dynamically yields chapters, adding `"Finale"` only when all 7 are completed.
- **Story Flags Supported**:
  - `knows_sana_contact`
  - `knows_kabir_meeting`
  - `knows_call_content`
  - `accused_kabir`
  - `found_fallout_evidence`

### [COMPLETE] Phase 3: Chapter Hub Screen & Transitions
- **7 Core Chapters**:
  1. *"The Plan"*
  2. *"The Watcher"*
  3. *"The Signal"*
  4. *"The Job"*
  5. *"The Getaway"*
  6. *"The Split"*
  7. *"The Fallout"*
- **Finale Climax**: Appears only once all 7 standard chapters are in `completed_chapters`.
- **Interactive Navigation (`hub.py`)**:
  - Keyboard navigation (Up/Down or W/S) with selection wrapping.
  - Enter or Space confirms selection.
  - Direct number-key shortcuts (1–7 for chapters, 8 for Finale).
  - Mouse hover highlighting and left-click selection.
  - Dynamic status badges: `[ AVAILABLE ]`, `[ COMPLETED ✓ ]`, and `[ UNLOCKED ]` for Finale.
- **Active Chapter Screen (`chapter_screen.py`)**:
  - Chapter title, briefing context, and status HUD.
  - Playable sprite exploration inside the chapter room.
  - `[C]` key / button to complete chapter.
  - `[H]` or `[ESC]` key / button to return to the Hub.

---

## 3. Test Suite Status
All unit tests passing (21 / 21):
- `test_game_state.py` (10 tests): Immutability, frozen dataclass safety, pure function returns, independent branches.
- `test_hub.py` (11 tests): Chapter list ordering, Finale lock/unlock conditions, keyboard navigation, number keys, mouse selection, chapter transitions.

---

## 4. Next Planned Steps
- **Phase 4**: Implement unique mini-mechanics and narrative clue interactions for each individual chapter.
- **Phase 5**: Branching dialogue trees and consequence resolution in the Finale.
