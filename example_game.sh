#!/bin/bash

# Example SoloGM Playthrough Script: Starfall Legacy
#
# This script executes the commands outlined in example_game.md.
# It echoes each command, waits briefly, and then runs it.
#
# Note: Some steps require manual interaction (like editor prompts or AI feedback loops)
#       or dynamic IDs (like specific event IDs). These are noted in comments.
#       For simple confirmations (like adding an oracle interpretation as an event),
#       this script uses `yes |` to automatically confirm 'y'.

# Function to echo, sleep, and run a command
run_cmd() {
    # Use "$@" to preserve arguments with spaces correctly
    echo "+ $@"
    sleep 0.5
    # Execute the command directly, letting the shell handle arguments
    "$@"
    echo # Add a newline for better readability
    sleep 0.5 # Pause after command execution too
}

# --- Initial Setup ---

echo "--- Initial Setup ---"
# Use standard shell quoting for arguments with spaces
run_cmd sologm game create --name "Starfall Legacy" --description "Searching for ancient Precursor technology in the forgotten sectors of the galaxy."
run_cmd sologm game info

# --- Act 1: The Xylar Signal ---

echo "--- Act 1: The Xylar Signal ---"
run_cmd sologm act create --title "The Xylar Signal" --summary "Investigating a mysterious energy signature detected near the abandoned moon Xylar."
run_cmd sologm act info

# --- Act 1, Scene 1: Arrival at Xylar ---

echo "--- Act 1, Scene 1: Arrival at Xylar ---"
run_cmd sologm scene add --title "Arrival at Xylar" --description "The starship 'Stardust Drifter' drops out of warp near the desolate moon Xylar. The signal source appears to be planetside."
run_cmd sologm scene info
run_cmd sologm event add --description "Scanners pick up faint energy fluctuations matching the signal from a derelict orbital station." --source manual
run_cmd sologm dice roll 1d20+3 --reason "Detailed scan of the orbital station"
run_cmd sologm oracle interpret --context "What is the immediate state of the derelict station?" --results "Silent, Power Fluctuations, Ancient Markings" --count 3
run_cmd sologm oracle status

# Note: The following command requires manual interaction for the editor (--edit)
# and potentially for the confirmation prompt afterwards.
# We remove 'yes |' because it breaks the interactive editor.
echo "+ sologm oracle select 2 --edit"
sleep 0.5
sologm oracle select 2 --edit
echo
sleep 0.5

run_cmd sologm event list --limit 5

# --- Act 1, Scene 2: Station Interior ---

echo "--- Act 1, Scene 2: Station Interior ---"
run_cmd sologm scene add --title "Station Interior" --description "Boarding the station. Halls are dark, filled with floating debris and strange glyphs."
run_cmd sologm scene list
run_cmd sologm dice roll 1d6 --reason "Navigating debris field inside the station"
run_cmd sologm event add --description "Successfully navigated the debris, finding a partially sealed door covered in the strange markings." --source dice
run_cmd sologm oracle interpret --context "What lies beyond the marked door?" --results "Faint Humming, Data Archive, Warning Signal"

echo "+ sologm oracle retry"
sleep 0.5
# Note: 'oracle retry' opens an editor, requiring manual interaction.
sologm oracle retry
echo
sleep 0.5

# Note: The following command requires manual confirmation [y/N]
# to add the selected interpretation as an event.
echo "+ sologm oracle select 1"
sleep 0.5
sologm oracle select 1
echo
sleep 0.5

echo "# Note: The following command requires a dynamic event ID."
echo "# You would typically get this ID from 'sologm event list' output."
echo "# Example: run_cmd sologm event edit --id evt_jklmno123"
echo "# Skipping this step in the automated script as the ID is unknown."
# run_cmd sologm event edit --id <event_id_from_list> # Requires manual interaction

run_cmd sologm dice history --limit 5

# --- Completing Act 1 ---

echo "--- Completing Act 1 ---"
# Use standard quoting for the context string
echo "+ sologm act complete --ai --context \"Focus on the discovery of the Precursor station and the mystery of the data archive. Keep the summary to 3 paragraphs.\""
sleep 0.5
# Note: 'act complete --ai' enters an interactive loop (Accept/Edit/Regenerate/Cancel).
# This requires manual user input (e.g., 'A').
sologm act complete --ai --context "Focus on the discovery of the Precursor station and the mystery of the data archive. Keep the summary to 3 paragraphs."
echo
sleep 0.5

# --- Act 2: Pursuit ---

echo "--- Act 2: Pursuit ---"
echo "+ sologm act create"
sleep 0.5
# Note: 'act create' without title/summary opens an editor, requiring manual interaction.
sologm act create
echo
sleep 0.5

run_cmd sologm scene add --title "Nebula Run" --description "Fleeing through a dense nebula, pursued by unidentified vessels."
run_cmd sologm event add --description "The 'Stardust Drifter' takes minor hull damage from weapon fire."

# --- Status Checks and Export ---

echo "--- Status Checks and Export ---"
run_cmd sologm game status

echo "+ sologm game edit"
sleep 0.5
# Note: 'game edit' without --id opens an editor for the active game, requiring manual interaction.
sologm game edit
echo
sleep 0.5

echo "+ sologm game dump"
sleep 0.5
sologm game dump # Just display the dump, not using run_cmd to avoid extra echo noise
echo
sleep 0.5

echo "+ sologm game dump --metadata --include-concepts"
sleep 0.5
sologm game dump --metadata --include-concepts # Just display the dump
echo
sleep 0.5

echo "--- Example Playthrough Script Complete ---"

# (Optional: Copy dump to clipboard for use with external AI)
# echo "+ sologm game dump | pbcopy # macOS example"
# sleep 0.5
# sologm game dump | pbcopy
# echo
# sleep 0.5
