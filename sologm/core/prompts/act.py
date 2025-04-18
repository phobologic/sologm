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
