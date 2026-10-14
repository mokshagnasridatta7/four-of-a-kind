# Four of a Kind — Narrative & Story Design

## Overview
"Four of a Kind" is a neo-noir crime thriller and heist story. Four criminal specialists execute a high-profile heist in the city, but conflicting loyalties, secret calls, and hidden agendas threaten to destroy them all from within.

---

## The Crew
1. **The Player (Operative)**: The boots-on-the-ground infiltration specialist. Calm under pressure, observes everything.
2. **Kabir (The Mastermind)**: Charismatic, methodical planner. Orchestrated the score, but holds private side meetings and keeps crucial ledger details hidden.
3. **Sana (The Hacker / Intel)**: Tech specialist handling surveillance taps, security overrides, and backchannel communication.
4. **The Enforcer / Lookout**: Secures the perimeter, manages crowd control and getaway routes.

---

## Chapters Overview

### Chapter 1: The Plan
The crew gathers in a dimly lit safehouse basement. Kabir presents blueprints for the city's private bank deposit vault. Roles are assigned, timing windows calculated, and getaway routes drafted.

### Chapter 2: The Watcher
High-rise rooftop surveillance overlooking the target facility. The player monitors security guard patrols, CCTV camera rotation cycles, and identifies blind spots in the perimeter.

### Chapter 3: The Signal
Underground comms setup. The player establishes a secured link with Sana, tapping into the local telephone relays and awaiting the green-light authorization before moving.
- *Narrative Flag*: `knows_sana_contact`

### Chapter 4: The Job
The infiltration. Breaching the vault during a timed sensor outage. Disabling laser grids and cracking the primary safe deposit lockbox.

### Chapter 5: The Getaway
Alarm tripped! Evasion through neon-lit alleys, avoiding police cruisers and road blocks to reach the designated extraction vehicle.

### Chapter 6: The Split
Rendezvous at the abandoned shipyard warehouse to divide the haul. Discrepancies appear in Kabir's cut and ledger notes. Suspicions surface within the crew.
- *Narrative Flag*: `knows_kabir_meeting`
- *Narrative Flag*: `accused_kabir`

### Chapter 7: The Fallout
The aftermath. Listening to intercepted wiretap recordings reveals Kabir's private negotiations to sell out the crew to an outside syndicate.
- *Narrative Flag*: `knows_call_content`
- *Narrative Flag*: `found_fallout_evidence`

---

## Finale (Unlocked after completing all 7 chapters)
The final showdown. Having uncovered the evidence, the player confronts Kabir at the drop point. The fate of the score and the surviving crew members is determined by the evidence collected and choices made.

---

## Key Story Flags
- `knows_sana_contact`: Sana's private encrypted comm channel discovered.
- `knows_kabir_meeting`: Witnessed Kabir meeting an unknown operative behind the diner.
- `knows_call_content`: Tapped audio confirms a planned betrayal.
- `accused_kabir`: The player openly questioned Kabir during the diamond division.
- `found_fallout_evidence`: Irrefutable physical proof of the sell-out contract.
