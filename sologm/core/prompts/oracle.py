"""Prompt templates for oracle interpretations."""

from typing import List, Optional


class OraclePrompts:
    """Prompt templates for oracle interpretations."""

    @staticmethod
    def format_events(recent_events: List[str]) -> str:
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
    def get_example_format() -> str:
        """Get example format for interpretations.

        Returns:
            Example interpretations to show the AI the expected format
        """
        return """## The Mysterious Footprints
The footprints suggest someone sneaked into the cellar during the night. Based on their size and depth, they likely belong to a heavier individual carrying something substantial - possibly the stolen brandy barrel.

## An Inside Job
The lack of forced entry and the selective theft of only the special brandy barrel suggests this was done by someone familiar with the cellar layout and the value of that specific barrel."""

    @staticmethod
    def format_previous_interpretations(
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
    def get_retry_text(retry_attempt: int) -> str:
        """Get retry-specific instructions.

        Args:
            retry_attempt: Current retry attempt number

        Returns:
            Text with retry-specific instructions
        """
        if retry_attempt <= 0:
            return ""
        return f"This is retry attempt #{retry_attempt + 1}. Please provide COMPLETELY DIFFERENT interpretations than those listed above."

    @classmethod
    def build_interpretation_prompt(
        cls,
        game_description: str,
        scene_description: str,
        recent_events: List[str],
        context: str,
        oracle_results: str,
        count: int,
        previous_interpretations: Optional[List[dict]] = None,
        retry_attempt: int = 0,
    ) -> str:
        """Build the complete prompt for interpretation generation.

        Args:
            game_description: Description of the current game
            scene_description: Description of the current scene
            recent_events: List of recent event descriptions
            context: User's question or context
            oracle_results: Oracle results to interpret
            count: Number of interpretations to generate
            previous_interpretations: Optional list of previous interpretations to avoid
            retry_attempt: Current retry attempt number

        Returns:
            Complete prompt for the AI
        """
        events_text = cls.format_events(recent_events)
        example_format = cls.get_example_format()
        previous_interps_text = cls.format_previous_interpretations(
            previous_interpretations, retry_attempt
        )
        retry_text = cls.get_retry_text(retry_attempt)

        return f"""You are interpreting oracle results for a solo RPG player.

Game: {game_description}
Current Scene: {scene_description}
Recent Events:
{events_text}

Player's Question/Context: {context}
Oracle Results: {oracle_results}

{previous_interps_text}
{retry_text}

Please provide {count} different interpretations of these oracle results.
Each interpretation should make sense in the context of the game and scene.
Be creative but consistent with the established narrative.

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
