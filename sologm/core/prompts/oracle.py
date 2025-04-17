"""Prompt templates for oracle interpretations."""

from typing import List, Optional

from sologm.models.scene import Scene


class OraclePrompts:
    """Prompt templates for oracle interpretations."""

    @staticmethod
    def build_interpretation_prompt(
        scene: Scene,
        context: str,
        oracle_results: str,
        count: int = 5,
        previous_interpretations: Optional[List[dict]] = None,
        retry_attempt: int = 0,
    ) -> str:
        """Build the complete prompt for interpretation generation.

        Args:
            scene: Scene object with loaded relationships
            context: User's question or context
            oracle_results: Oracle results to interpret
            count: Number of interpretations to generate
            previous_interpretations: Optional list of previous interpretations to avoid
            retry_attempt: Current retry attempt number

        Returns:
            Complete prompt for the AI
        """
        # Access related models through relationships
        act = scene.act
        game = act.game

        # Get recent events through scene relationship (limited to 5)
        recent_events = [event.description for event in scene.events[:5]]

        # Format the events
        events_text = OraclePrompts._format_events(recent_events)

        # Get example format
        example_format = OraclePrompts._get_example_format()

        # Format previous interpretations if any
        previous_interps_text = OraclePrompts._format_previous_interpretations(
            previous_interpretations, retry_attempt
        )

        # Get retry-specific text if applicable
        retry_text = OraclePrompts._get_retry_text(retry_attempt)

        # Build the complete prompt
        return f"""You are interpreting oracle results for a solo RPG player.

Game: {game.description or ""}
Act: {act.summary or ""}
Current Scene: {scene.description or ""}
Recent Events:
{events_text}

Player's Question/Context: {context}
Oracle Results: {oracle_results}

{previous_interps_text}
{retry_text}

Please provide {count} different interpretations of these oracle results.
Each interpretation should make sense in the context of the game and scene.
Be creative but consistent with the established narrative.  Each potential
interpretation should be 3-5 sentences long, and full of vivid imagery.

Format your response using Markdown headers exactly as follows:

```markdown
## [Title of first interpretation]
[Detailed description of first interpretation]

## [Title of second interpretation]
[Detailed description of second interpretation]

[and so on for each interpretation]
```

Here's an example of the format:

{example_format}

Important:
- Start each interpretation with "## " followed by a descriptive title
- Then provide the detailed description on the next line(s)
- Make sure to separate interpretations with a blank line
- Do not include any text outside this format
- Do not include the ```markdown and ``` delimiters in your actual response
- Do not number the interpretations
"""

    @staticmethod
    def _format_events(recent_events: List[str]) -> str:
        """Format recent events for the prompt.

        Args:
            recent_events: List of recent event descriptions

        Returns:
            Formatted events text for the prompt
        """
        if not recent_events:
            return "No recent events"
        return "\n".join([f"- {event}" for event in recent_events])

    @staticmethod
    def _get_example_format() -> str:
        """Get example format for interpretations.

        Returns:
            Example interpretations to show the AI the expected format
        """
        return """## The Mysterious Footprints
The footprints suggest someone sneaked into the cellar during the night. Based on their size and depth, they likely belong to a heavier individual carrying something substantial - possibly the stolen brandy barrel.

## An Inside Job
The lack of forced entry and the selective theft of only the special brandy barrel suggests this was done by someone familiar with the cellar layout and the value of that specific barrel."""

    @staticmethod
    def _format_previous_interpretations(
        previous_interpretations: Optional[List[dict]], retry_attempt: int
    ) -> str:
        """Format previous interpretations for the prompt.

        Args:
            previous_interpretations: List of previous interpretations to avoid repeating
            retry_attempt: Current retry attempt number

        Returns:
            Formatted previous interpretations section
        """
        if not previous_interpretations or retry_attempt <= 0:
            return ""

        text = "\n=== PREVIOUS INTERPRETATIONS (DO NOT REPEAT THESE) ===\n\n"
        for interp in previous_interpretations:
            text += f"## {interp['title']}\n{interp['description']}\n\n"
        text += "=== END OF PREVIOUS INTERPRETATIONS ===\n\n"
        return text

    @staticmethod
    def _get_retry_text(retry_attempt: int) -> str:
        """Get retry-specific instructions.

        Args:
            retry_attempt: Current retry attempt number

        Returns:
            Text with retry-specific instructions
        """
        if retry_attempt <= 0:
            return ""
        return f"This is retry attempt #{retry_attempt + 1}. Please provide COMPLETELY DIFFERENT interpretations than those listed above."
