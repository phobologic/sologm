# Example SoloGM Playthrough: Starfall Legacy

This document outlines a sequence of `sologm` commands demonstrating a playthrough of a fictional space fantasy game called "Starfall Legacy". This example aims to touch upon many features, including game/act/scene management, events, dice rolls, and oracle interpretations (including AI use).

Where possible, slugs derived from titles (like `starfall-legacy`) are used. For things like specific events or interpretation sets, their IDs are generated dynamically (e.g., `evt_...`, `set_...`), so interactions might use those dynamic IDs or sequence numbers (like selecting interpretation `1`).

**Note:** The output shown after each command is illustrative. Actual output will include dynamic IDs and potentially different AI results.

---

## Initial Setup

**Create the game.** This also activates it.

```bash
sologm game create --name "Starfall Legacy" --description "Searching for ancient Precursor technology in the forgotten sectors of the galaxy."
```
*Output: Success message with game details.*

**Check the game info.**

```bash
sologm game info
```
*Output: Shows game name, description, ID, active status, no acts/scenes yet.*

---

## Act 1: The Xylar Signal

**Create the first act.** This also activates it. We'll provide title/summary directly here.

```bash
sologm act create --title "The Xylar Signal" --summary "Investigating a mysterious energy signature detected near the abandoned moon Xylar."
```
*Output: Success message with act details (Sequence 1, Active).*

**Check the act info.**

```bash
sologm act info
```
*Output: Shows details for "The Xylar Signal", no scenes yet.*

---

## Act 1, Scene 1: Arrival at Xylar

**Add the first scene to the current act.** This also makes it the current scene.

```bash
sologm scene add --title "Arrival at Xylar" --description "The starship 'Stardust Drifter' drops out of warp near the desolate moon Xylar. The signal source appears to be planetside."
```
*Output: Success message with scene details (Sequence 1, Active).*

**Check the scene info** (includes events by default).

```bash
sologm scene info
```
*Output: Shows scene details, likely says "No events yet".*

**Add the first event manually.**

```bash
sologm event add --description "Scanners pick up faint energy fluctuations matching the signal from a derelict orbital station." --source manual
```
*Output: Success message, displays the added event in a table.*

**Roll dice for a sensor check.**

```bash
sologm dice roll 1d20+3 --reason "Detailed scan of the orbital station"
```
*Output: Displays the dice roll notation, individual results, modifier, total, reason, and associated scene ID.*

**Use the oracle to determine the station's condition.**

```bash
sologm oracle interpret --context "What is the immediate state of the derelict station?" --results "Silent, Power Fluctuations, Ancient Markings" --count 3
```
*Output: Shows "Generating interpretations...", then displays a table with 3 AI-generated interpretations (e.g., 1: Eerily quiet but unstable power suggests traps; 2: Ancient symbols hint at non-human origin; 3: Power surges indicate automated defenses might activate). Includes the Interpretation Set ID (e.g., `set_abc123`).*

**Check the current oracle status.**

```bash
sologm oracle status
```
*Output: Shows the details of the Interpretation Set generated above (`set_abc123`) and lists its interpretations again.*

**Select the second interpretation to become an event.** We use the sequence number '2'. It will prompt to confirm adding as an event. Let's assume we also want to edit the description slightly using the `--edit` flag.

```bash
sologm oracle select 2 --edit
```
*Output: Shows the selected interpretation. Prompts "Add this interpretation as an event?". Confirm [y/N]: y.*
*        Opens editor pre-filled with default description (Question, Oracle, Interpretation). Edit if desired. Save and close.*
*Output: Success message, displays the newly created event (linked to the interpretation).*

**List recent events** to see both manual and oracle-derived ones.

```bash
sologm event list --limit 5
```
*Output: Table showing the initial manual event and the event created from the oracle interpretation.*

## Act 1, Scene 2: Station Interior

**Add the second scene.** It automatically becomes the current scene.

```bash
sologm scene add --title "Station Interior" --description "Boarding the station. Halls are dark, filled with floating debris and strange glyphs."
```
*Output: Success message with scene details (Sequence 2, Active).*

**List scenes in the current act.**

```bash
sologm scene list
```
*Output: Table showing "Arrival at Xylar" (Completed) and "Station Interior" (Active).*

**Roll dice to navigate the debris.**

```bash
sologm dice roll 1d6 --reason "Navigating debris field inside the station"
```
*Output: Dice roll result.*

**Add an event based on the dice roll outcome** (manual description).

```bash
sologm event add --description "Successfully navigated the debris, finding a partially sealed door covered in the strange markings." --source dice
```
*Output: Success message, displays event.*

**Use the oracle again.**

```bash
sologm oracle interpret --context "What lies beyond the marked door?" --results "Faint Humming, Data Archive, Warning Signal"
```
*Output: Generates a new Interpretation Set (e.g., `set_def456`) with interpretations.*

**Let's pretend the interpretations weren't quite right. Retry, editing the context first.**

```bash
sologm oracle retry
```
*Output: Opens editor pre-filled with the *previous* context ("What lies beyond...") and results ("Faint Humming...").*
*        Modify the context (e.g., "What is the primary function of the room beyond the marked door?"). Save and close.*
*Output: "Generating new interpretations...", displays a new set (e.g., `set_ghi789`) based on the edited context.*

**Select the first interpretation from the *new* set.**

```bash
sologm oracle select 1
```
*Output: Shows interpretation, prompts to add as event. Confirm [y/N]: y.*
*Output: Success message, displays new event.*

**Edit the *first* event added in this scene** (the navigation one). We need its dynamic ID (e.g., `evt_jkl...`). Let's assume we found it via `sologm event list`. (If we didn't know the ID, `sologm event edit` without `--id` would edit the *most recent* event).

```bash
# Example: sologm event edit --id evt_jklmno123
# (Replace evt_jklmno123 with the actual ID from 'sologm event list')
sologm event edit --id <event_id_from_list>
```
*Output: Opens editor for the specified event. Make changes, save, close.*
*Output: Success message.*

**Check dice roll history for the current scene.**

```bash
sologm dice history --limit 5
```
*Output: Shows the 1d6 roll made earlier in this scene.*

**Complete the second scene.**

```bash
sologm scene complete
```
*Output: Success message.*

---

## Completing Act 1

**Complete the current act using AI summarization.** Provide some context to guide the AI.

```bash
sologm act complete --ai --context "Focus on the discovery of the Precursor station and the mystery of the data archive. Keep the summary to 3 paragraphs."
```
*Output: "Generating summary with AI...". Displays AI-generated Title and Summary.*
*        Prompts: "[A]ccept / [E]dit / [R]egenerate / [C]ancel?".*
*        Choose 'A' (Accept), 'E' (Edit in editor), or 'R' (Regenerate, possibly with feedback).*
*        Let's assume we Accept 'A'.*
*Output: Success message indicating Act 1 is complete with the chosen title/summary.*

---

## Act 2: Pursuit

**Create the second act.** This opens the editor for title/summary.

```bash
sologm act create
```
*Output: Opens editor. Enter Title: "Pursuit" and Summary: "Escaping the station as unknown ships arrive, deciphering the data.". Save and close.*
*Output: Success message for Act 2 creation (Sequence 2, Active).*

**Add a scene to Act 2.**

```bash
sologm scene add --title "Nebula Run" --description "Fleeing through a dense nebula, pursued by unidentified vessels."
```
*Output: Success message.*

**Add an event.**

```bash
sologm event add --description "The 'Stardust Drifter' takes minor hull damage from weapon fire."
```
*Output: Success message.*

---

## Status Checks and Export

**Check the overall game status.**

```bash
sologm game status
```
*Output: Detailed status showing active game ("Starfall Legacy"), active act ("Pursuit"), active scene ("Nebula Run"), recent events from the current scene, recent dice rolls (if any in current scene), etc.*

**Edit the game description** (opens editor).

```bash
sologm game edit
```
*Output: Opens editor with current name/description. Modify, save, close.*
*Output: Success message.*

**Dump the entire game log to markdown format on the console.**

```bash
sologm game dump
```
*Output: Prints the full game structure (Game -> Acts -> Scenes -> Events) as markdown.*

**Dump the game including metadata and concept explanations.**

```bash
sologm game dump --metadata --include-concepts
```
*Output: Prints markdown including IDs, timestamps, and the introductory concept explanations.*

**(Optional: Copy dump to clipboard for use with external AI)**

```bash
# macOS example
sologm game dump | pbcopy
```

---
*End of Example Playthrough*
