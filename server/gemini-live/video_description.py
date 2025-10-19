"""
Video Description using Gemini Live API

Processes a video file (with audio) and outputs real-time descriptions using Gemini's Live API.

Installation:
pip install google-genai moviepy pillow

Usage:
python video_description.py path/to/video.mp4
"""

import os
import asyncio
import base64
import io
import sys

import PIL.Image
from moviepy import VideoFileClip
import numpy as np

from google import genai
from google.genai import types

SEND_SAMPLE_RATE = 16000
MODEL = "models/gemini-2.0-flash-exp"  # Try a more general model

client = genai.Client(
    http_options={"api_version": "v1beta"},
    api_key=os.environ.get("GEMINI_API_KEY"),
)

CONFIG = types.LiveConnectConfig(
    response_modalities=["TEXT"],  # We want text descriptions
    media_resolution="MEDIA_RESOLUTION_MEDIUM",
    system_instruction=types.Content(
        parts=[types.Part(text="You are a video analysis assistant. When you receive video frames, describe what you see in detail including objects, people, actions, scenes, and any relevant context.")]
    ),
)


async def describe_video(video_path: str):
    """
    Process video file and output descriptions using Gemini Live API.

    Args:
        video_path: Path to video file
    """
    print(f"Loading video: {video_path}")
    clip = VideoFileClip(video_path)

    out_queue = asyncio.Queue(maxsize=10)

    async def send_frames():
        """Extract and send video frames at 1 FPS with real-time pacing."""
        duration = min(clip.duration, 10.0)  # Limit to 10 seconds for testing
        frame_interval = 1.0  # 1 FPS as recommended by docs

        print(f"[Sending {int(duration)} frames...]")
        for t in np.arange(0, duration, frame_interval):
            frame = clip.get_frame(t)

            # Convert to PIL Image and resize to recommended 768x768
            img = PIL.Image.fromarray(frame)
            img.thumbnail([768, 768])

            # Encode as JPEG
            image_io = io.BytesIO()
            img.save(image_io, format="jpeg")
            image_io.seek(0)
            image_bytes = image_io.read()

            await out_queue.put({
                "mime_type": "image/jpeg",
                "data": base64.b64encode(image_bytes).decode()
            })

            print(f"[Sent frame at {t:.1f}s]", flush=True)
            # Wait 1 second before sending next frame (real-time pacing)
            await asyncio.sleep(1.0)

        print("\n[Video frames complete]")

    async def send_audio():
        """Extract and send audio chunks with proper timing."""
        if clip.audio is None:
            print("[No audio track in video]")
            return

        # Get audio as array at 16kHz (required by Live API)
        audio_array = clip.audio.to_soundarray(fps=SEND_SAMPLE_RATE)

        # Convert to mono if stereo
        if len(audio_array.shape) > 1:
            audio_array = audio_array.mean(axis=1)

        # Convert to int16 PCM format
        audio_array = (audio_array * 32767).astype(np.int16)

        # Send in chunks with real-time pacing
        chunk_size = 1024  # samples
        chunk_duration = chunk_size / SEND_SAMPLE_RATE  # seconds per chunk

        for i in range(0, len(audio_array), chunk_size):
            chunk = audio_array[i:i+chunk_size]
            await out_queue.put({
                "mime_type": "audio/pcm",
                "data": chunk.tobytes()
            })

            # Wait appropriate time before sending next chunk (real-time pacing)
            await asyncio.sleep(chunk_duration)

        print("\n[Audio complete]")

    async def send_to_session(session):
        """Send queued data to Gemini Live API session."""
        frames_sent = 0
        total_frames = 10  # We're sending 10 frames

        while True:
            msg = await out_queue.get()
            if msg is None:
                break
            # Handle text prompts vs media data
            if isinstance(msg, tuple) and msg[0] == "text":
                # Send text with end_of_turn to trigger model response
                await session.send(input=msg[1], end_of_turn=True)
            else:
                # Send frame
                frames_sent += 1
                is_last_frame = (frames_sent == total_frames)
                # End turn after last frame so model knows to respond
                await session.send(input=msg, end_of_turn=is_last_frame)

    async def receive_descriptions(session):
        """Receive and print text descriptions from Gemini (ignore audio)."""
        print("\n=== Video Descriptions ===\n")

        # Open output file
        output_file = video_path.rsplit('.', 1)[0] + '_description.txt'
        descriptions = []

        try:
            while True:
                turn = session.receive()
                async for response in turn:
                    # Print and save text descriptions
                    if text := response.text:
                        print(text, end="", flush=True)
                        descriptions.append(text)
                    # Ignore audio data (we only want text descriptions)
                    if response.data:
                        pass  # Skip audio
                print()  # New line after each turn
        except Exception as e:
            if "closed" not in str(e).lower():
                print(f"[Receive error: {e}]")
                raise
        finally:
            # Write all descriptions to file
            if descriptions:
                with open(output_file, 'w') as f:
                    f.write(''.join(descriptions))
                print(f"\n[Saved description to: {output_file}]")

    # Run with Gemini Live API
    async with client.aio.live.connect(model=MODEL, config=CONFIG) as session:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(send_frames())
            tg.create_task(send_audio())
            tg.create_task(send_to_session(session))
            tg.create_task(receive_descriptions(session))

    clip.close()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python video_description.py <video_path>")
        sys.exit(1)

    video_path = sys.argv[1]

    if not os.path.exists(video_path):
        print(f"Error: Video file not found: {video_path}")
        sys.exit(1)

    if not os.environ.get("GEMINI_API_KEY"):
        print("Error: GEMINI_API_KEY environment variable not set")
        sys.exit(1)

    asyncio.run(describe_video(video_path))
