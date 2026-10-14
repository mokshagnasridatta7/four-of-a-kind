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

### [COMPLETE] Phase 4: Playable Level — Chapter 1: The Plan (`level_plan.py`)
- **Safehouse Heist Room Environment**:
  - Playable sprite moves freely through the safehouse planning room.
  - Interactive physical stations: Blueprint Map Table (Route), Schedule Terminal (Timing), Gear Workbench (Tool).
  - Master Planning Board with 3 decision slots and interactive selection modals.
- **Combination Puzzle (3 Choices Each)**:
  - **Route**: Rooftop Ventilation Shaft, Underground Service Tunnel, Disguised Delivery Dock.
  - **Timing**: 02:15 AM Patrol Shift Rotation, 03:30 AM System Diagnostic Reboot, 04:45 AM Pre-dawn Delivery Window.
  - **Tool**: Thermal Lance, EMP Disruptor, Biometric Keycloner.
- **Hidden Interactive Detail**:
  - Tucked-away discarded burner radio behind the server rack with a pulsing signal LED.
  - Investigating (`[E]` / click) reveals Sana's encrypted frequency note (`142.85 MHz`) and sets `knows_sana_contact` flag via `set_flag(state, FLAG_KNOWS_SANA_CONTACT)`.
- **Puzzle Completion & Hub Return**:
  - Once all 3 options are selected, player executes the plan (`[SPACE]` / `[ENTER]` / Click).
  - Calls `complete_chapter(state, "The Plan")` and sets `current_chapter = None`, returning to the Hub regardless of whether the secret flag was found.

### [COMPLETE] Phase 5: Playable Level — Chapter 2: The Watcher (`level_watcher.py`)
- **Rooftop Surveillance Environment**:
  - Overlook overlooking the ground facility: main gate, courtyard vault entrance, and back service alley.
  - Rooftop observation deck with 3 designated observation zones along the parapet edge and a safe cover area.
- **3-Day Guard Patrol & Stealth Observation**:
  - Ground guard patrols with an oscillating searchlight beam.
  - Player observes at the edge to fill the day's patrol progress bar.
  - If illuminated at the edge, detection rises. Stepping back into cover drops detection to 0%.
  - Being spotted triggers a red alert and resets the current day attempt without ending the chapter or kicking to the hub.
- **Scripted Kabir Meeting Event**:
  - During Day 2 (between 30% and 75% progress), Kabir slips into the Back Service Alley to meet an unfamiliar contact.
  - Observing Zone 3 (Back Alley) witnesses the clandestine meeting, triggers a dialogue sequence, and sets `knows_kabir_meeting` flag via `set_flag(state, FLAG_KNOWS_KABIR_MEETING)`.
- **Chapter Completion**:
  - Successfully mapping all 3 days calls `complete_chapter(state, "The Watcher")` and sets `current_chapter = None`, returning to the Hub regardless of whether the secret flag was found.

---

## 3. Test Suite Status
All unit tests passing (37 / 37):
- `test_game_state.py` (10 tests): Immutability, frozen dataclass safety, pure function returns, independent branches.
- `test_hub.py` (11 tests): Chapter list ordering, Finale lock/unlock conditions, keyboard navigation, number keys, mouse selection, chapter transitions.
- `test_plan_level.py` (8 tests): Puzzle short-lists, partial/full selection checks, hidden detail `knows_sana_contact` flag acquisition, completion flow with and without secret.
- `test_watcher_level.py` (8 tests): Stealth detection, cover vs observing states, observation zones, day retry reset, Kabir meeting flag acquisition, completion flow with and without secret.

---

## 4. Next Planned Steps
- **Phase 6**: Build Chapter 3: "The Signal" (intercepting radio frequencies and hacking telecom relays).
- **Phase 7**: Build remaining chapter gameplay and the unlocked Finale confrontation.
