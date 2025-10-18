"""
Simple Video Description using Gemini API (not Live API)

This approach uploads the video file directly to Gemini and gets a description.

Installation:
pip install google-genai

Usage:
python simple_video_description.py path/to/video.mp4
"""

import os
import sys
import time

from google import genai
from google.genai import types

# Initialize client
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

def describe_video(video_path: str):
    """
    Upload video and get description from Gemini.

    Args:
        video_path: Path to video file
    """
    print(f"Uploading video: {video_path}")

    # Upload the video file
    with open(video_path, 'rb') as f:
        video_file = client.files.upload(file=f, config={"mime_type": "video/mp4"})
    print(f"Uploaded file: {video_file.name}")

    # Wait for file to be processed
    print("Waiting for video to be processed...")
    while video_file.state == "PROCESSING":
        time.sleep(2)
        video_file = client.files.get(name=video_file.name)

    if video_file.state == "FAILED":
        raise ValueError(f"Video processing failed: {video_file.error}")

    print("Video processed successfully!")

    # Generate description
    print("\n=== Generating Description ===\n")

    response = client.models.generate_content(
        model="gemini-2.0-flash-exp",
        contents=[
            types.Content(
                role="user",
                parts=[
                    types.Part.from_uri(file_uri=video_file.uri, mime_type=video_file.mime_type),
                    types.Part(text="Describe this video in detail. Include what you see, any actions taking place, the setting, and any other relevant details."),
                ],
            ),
        ],
    )

    description = response.text
    print(description)

    # Save to file
    output_file = video_path.rsplit('.', 1)[0] + '_description.txt'
    with open(output_file, 'w') as f:
        f.write(description)

    print(f"\n[Saved description to: {output_file}]")

    # Clean up
    client.files.delete(name=video_file.name)
    print(f"[Cleaned up uploaded file]")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_video_description.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    describe_video(video_path)
