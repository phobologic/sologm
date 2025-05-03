"""Prompt templates for act-related AI interactions."""

from typing import Dict


class ActPrompts:
    """Prompt templates for act summaries and other act-related AI tasks."""

    @staticmethod
    def build_summary_prompt(act_data: Dict) -> str:
        """Build the prompt for generating an act summary.

        Args:
            act_data: Structured data about the act, including game, scenes, and events

        Returns:
            String prompt for AI model
        """
        game = act_data["game"]
        act = act_data["act"]
        scenes = act_data["scenes"]
        additional_context = act_data.get("additional_context")

        # Build the prompt
        prompt = f"""You are an expert storyteller and narrative analyst. I need you to create a concise summary and title for an act in a tabletop roleplaying game.

GAME INFORMATION:
Title: {game["name"]}
Description: {game["description"]}

ACT INFORMATION:
Sequence: Act {act["sequence"]}
Current Title: {act["title"] or "Untitled"}
Current Summary: {act["summary"] or "No summary"}

SCENES IN THIS ACT:
"""

        # Add scenes and their events
        for scene in scenes:
            prompt += f"\nSCENE {scene['sequence']}: {scene['title'] or 'Untitled'}\n"
            prompt += f"Description: {scene['description'] or 'No description'}\n"

            if scene["events"]:
                prompt += "Events:\n"
                for event in scene["events"]:
                    prompt += f"- {event['description']}\n"
            else:
                prompt += "No events recorded for this scene.\n"

        # Add additional context if provided, with special handling for regeneration requests
        if additional_context:
            # Check if this is a regeneration request (contains PREVIOUS GENERATION)
            if "PREVIOUS GENERATION:" in additional_context:
                prompt += f"\nREGENERATION REQUEST:\n{additional_context}\n"
            else:
                prompt += f"\nADDITIONAL CONTEXT:\n{additional_context}\n"

        # Add instructions
        prompt += """
TASK:
1. Create a compelling title for this act (1-7 words)
2. Write a concise summary of the act (3-5 paragraphs)

The title should capture the essence or theme of the act.
The summary should highlight key events, character developments, and narrative arcs.

Format your response exactly as follows:

TITLE: [Your suggested title]

SUMMARY:
[Your 3-5 paragraph summary]

Do not include any other text or explanations outside this format.
"""

        return prompt

    @staticmethod
    def parse_summary_response(response: str) -> Dict[str, str]:
        """Parse the response from the AI model.

        Args:
            response: Text response from AI model

        Returns:
            Dict with title and summary
        """
        # Default values
        title = ""
        summary = ""

        # Parse the response
        lines = response.strip().split("\n")

        # Extract title
        for i, line in enumerate(lines):
            if line.startswith("TITLE:"):
                title = line[6:].strip()
                break

        # Extract summary
        summary_start = False
        summary_lines = []

        for line in lines:
            if line.startswith("SUMMARY:"):
                summary_start = True
                continue

            if summary_start:
                summary_lines.append(line)

        summary = "\n".join(summary_lines).strip()

        return {
            "title": title,
            "summary": summary,
        }

    @staticmethod
    def build_narrative_prompt(narrative_data: Dict) -> str:
        """Build the prompt for generating an act narrative.

        Args:
            narrative_data: Structured data including game, act, previous act summary,
                            scenes with events, and optional user guidance.

        Returns:
            String prompt for the AI model to generate a narrative.
        """
        game = narrative_data["game"]
        act = narrative_data["act"]
        previous_act_summary = narrative_data.get("previous_act_summary")
        scenes = narrative_data["scenes"]
        user_guidance = narrative_data.get("user_guidance")

        prompt = """You are a master storyteller tasked with writing a narrative chapter based on the following game events. Your goal is to weave the structured information into a compelling prose story in Markdown format.

GAME INFORMATION:
Title: {game_name}
Description: {game_description}
""".format(
            game_name=game.get("name", "Untitled Game"),
            game_description=game.get("description", "No description provided."),
        )

        if previous_act_summary:
            prompt += f"""
PREVIOUS ACT SUMMARY (Context):
{previous_act_summary}
"""

        prompt += f"""
CURRENT ACT INFORMATION:
Sequence: Act {act.get("sequence", "?")}
Title: {act.get("title", "Untitled Act")}
Summary: {act.get("summary", "No summary provided.")}

SCENES IN THIS ACT:
"""

        if not scenes:
            prompt += "No scenes recorded for this act.\n"
        else:
            for scene in scenes:
                prompt += f"\nSCENE {scene.get('sequence', '?')}: {scene.get('title', 'Untitled Scene')}\n"
                prompt += f"Description: {scene.get('description', 'No description')}\n"

                events = scene.get("events", [])
                if events:
                    prompt += "Events (in chronological order):\n"
                    for event in events:
                        source = event.get("source_name", "Unknown source")
                        description = event.get("description", "No description")
                        prompt += f"- ({source}): {description}\n"
                else:
                    prompt += "No events recorded for this scene.\n"

        if user_guidance:
            prompt += "\nUSER GUIDANCE:\n"
            for key, value in user_guidance.items():
                if value:  # Only include guidance if a value was provided
                    prompt += f"- {key.replace('_', ' ').title()}: {value}\n"

        prompt += """
TASK:
Write a compelling narrative for the current act based on all the information provided (game context, previous act summary, current act scenes/events, and user guidance).
The narrative should flow logically, connecting the events into a coherent story.
Use the user guidance to shape the tone, style, focus, and point of view.
Output the entire narrative in **Markdown format**.
Do not include any introductory phrases like "Here is the narrative:" or summaries of your own work. Just provide the Markdown narrative itself.
"""
        return prompt

    @staticmethod
    def build_narrative_regeneration_prompt(
        narrative_data: Dict, previous_narrative: str, feedback: str
    ) -> str:
        """Build the prompt for regenerating an act narrative with feedback.

        Args:
            narrative_data: Structured data (same as build_narrative_prompt).
            previous_narrative: The previously generated narrative text.
            feedback: User's feedback on the previous narrative.

        Returns:
            String prompt for the AI model to regenerate a narrative.
        """
        # Reuse the initial prompt structure but modify the task
        base_prompt = ActPrompts.build_narrative_prompt(narrative_data)

        # Find the TASK section and insert regeneration context before it
        task_marker = "\nTASK:\n"
        task_index = base_prompt.find(task_marker)

        if task_index == -1:
            # Fallback if TASK marker isn't found (shouldn't happen)
            regeneration_context = f"""
PREVIOUS NARRATIVE:
{previous_narrative}

USER FEEDBACK ON PREVIOUS NARRATIVE:
{feedback}
"""
            prompt = base_prompt + regeneration_context + task_marker + """Generate a *new* narrative for the act. Carefully consider the user's feedback provided above and incorporate it into the revised narrative, while still adhering to the original context and user guidance. Output the *entire new* narrative in **Markdown format**. Do not just describe the changes. Do not include any introductory phrases. Just provide the new Markdown narrative."""
        else:
            regeneration_context = f"""
PREVIOUS NARRATIVE:
{previous_narrative}

USER FEEDBACK ON PREVIOUS NARRATIVE:
{feedback}
"""
            prompt = (
                base_prompt[:task_index]
                + regeneration_context
                + task_marker
                + """Generate a *new* narrative for the act. Carefully consider the user's feedback provided above and incorporate it into the revised narrative, while still adhering to the original context and user guidance (unless the feedback specifically overrides it). Output the *entire new* narrative in **Markdown format**. Do not just describe the changes. Do not include any introductory phrases. Just provide the new Markdown narrative."""
            )

        return prompt
