"""Centralized prompts for Gemini AI analysis.

Edit these prompts to change how the AI analyzes different types of content.
"""

# IMAGE ANALYSIS PROMPT
IMAGE_PROMPT = """Describe what's happening in this image. Focus on:
- What is shown in the image
- Any issues or problems visible (e.g., damage, graffiti, broken items)
- Location details if visible (street signs, addresses, landmarks)
- Any other relevant details

{context}

Provide a clear, concise description in 2-3 sentences."""


# VIDEO ANALYSIS PROMPT (used as system instruction for Gemini Live)
VIDEO_PROMPT = """Analyze this video and describe what's happening. Focus on:
- Main subjects and actions in the video
- Any issues or problems visible
- Location or environment details
- Audio content if present

Provide a clear, concise description in 2-3 sentences."""
