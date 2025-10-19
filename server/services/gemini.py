"""Gemini AI tools: analyze content (text, image, video) to understand what's happening."""
import asyncio
import base64
import io
from typing import Optional, Union
from pathlib import Path

import PIL.Image
import google.generativeai as genai
from google import genai as genai_live
from google.genai import types

try:
    from server.config import config
    from server.prompts import IMAGE_PROMPT, VIDEO_PROMPT
except ModuleNotFoundError:
    # Fall back to relative import (for Railway deployment)
    from config import config
    from prompts import IMAGE_PROMPT, VIDEO_PROMPT

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)


class GeminiModels:
    """Available models."""
    FLASH = 'gemini-2.5-flash'
    PRO = 'gemini-2.5-pro'
    FLASH_LITE = 'gemini-2.5-flash-lite'
    LIVE_FLASH = 'models/gemini-2.0-flash-exp'


# Dictionary version for API endpoints
GEMINI_MODELS = {
    'FLASH': GeminiModels.FLASH,
    'PRO': GeminiModels.PRO,
    'FLASH_LITE': GeminiModels.FLASH_LITE,
    'LIVE_FLASH': GeminiModels.LIVE_FLASH
}


async def analyze_image(
    image_data: Union[bytes, str, Path],
    text: Optional[str] = None,
    model: str = GeminiModels.FLASH) -> Optional[str]:
    """Analyze image (with optional text) and describe what's happening."""
    try:
        if isinstance(image_data, (str, Path)):
            img = PIL.Image.open(image_data)
        else:
            img = PIL.Image.open(io.BytesIO(image_data))

        context = f'Additional context from message: "{text}"' if text else ''
        prompt = IMAGE_PROMPT.format(context=context)

        response = genai.GenerativeModel(model).generate_content([prompt, img])
        return response.text.strip()
    except Exception as e:
        print(f"❌ Error in analyze_image: {e}")
        import traceback
        traceback.print_exc()
        return None

async def analyze_video(
    video_data: Union[bytes, str, Path],
    model: str = GeminiModels.LIVE_FLASH,
    max_duration: float = 10.0) -> Optional[str]:
    """Analyze video using Gemini Live API and describe what's happening."""
    try:
        from moviepy import VideoFileClip
        import numpy as np
    except ImportError:
        print('❌ [VIDEO] Install: pip install moviepy pillow numpy')
        return None

    import tempfile
    import os

    temp_path = None
    try:
        # Handle bytes input - write to temp file
        if isinstance(video_data, bytes):
            fd, temp_path = tempfile.mkstemp(suffix=".mp4")
            os.close(fd)
            with open(temp_path, "wb") as f:
                f.write(video_data)
            video_path = temp_path
        else:
            video_path = str(video_data)

        clip = VideoFileClip(video_path)

        client = genai_live.Client(
            http_options={"api_version": "v1beta"},
            api_key=config.GEMINI_API_KEY
        )

        config_live = types.LiveConnectConfig(
            response_modalities=["TEXT"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            system_instruction=types.Content(
                parts=[types.Part(text=VIDEO_PROMPT)]
            )
        )

        queue = asyncio.Queue(maxsize=20)
        result = None

        async def send_frames():
            duration = min(clip.duration, max_duration)
            for t in np.arange(0, duration, 1.0):  # 1 FPS
                frame = clip.get_frame(t)
                img = PIL.Image.fromarray(frame)
                img.thumbnail([768, 768])

                buf = io.BytesIO()
                img.save(buf, format="jpeg")

                await queue.put({
                    "mime_type": "image/jpeg",
                    "data": base64.b64encode(buf.getvalue()).decode()
                })
                await asyncio.sleep(1.0)

        async def send_audio():
            if not clip.audio:
                return

            audio = clip.audio.to_soundarray(fps=16000)
            if len(audio.shape) > 1:
                audio = audio.mean(axis=1)
            audio = (audio * 32767).astype(np.int16)

            chunk_size = 1024
            for i in range(0, len(audio), chunk_size):
                await queue.put({
                    "mime_type": "audio/pcm",
                    "data": audio[i:i+chunk_size].tobytes()
                })
                await asyncio.sleep(chunk_size / 16000)

        async def send_to_session(session):
            frames = int(min(clip.duration, max_duration))
            count = 0
            while True:
                msg = await queue.get()
                if msg is None:
                    break
                count += 1
                await session.send(input=msg, end_of_turn=(count >= frames))

        async def receive(session):
            nonlocal result
            full_text = []
            try:
                while True:
                    turn = session.receive()
                    async for response in turn:
                        if response.text:
                            full_text.append(response.text)
            except:
                pass
            result = ''.join(full_text).strip()

        async with client.aio.live.connect(model=model, config=config_live) as session:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(send_frames())
                tg.create_task(send_audio())
                tg.create_task(send_to_session(session))
                tg.create_task(receive(session))

        clip.close()

        # Clean up temp file if created
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)

        return result

    except Exception as e:
        print(f'❌ [VIDEO] {e}')
        # Clean up temp file if created
        if temp_path and os.path.exists(temp_path):
            os.unlink(temp_path)
        return None

async def fetch_media_bytes(url: str) -> Optional[bytes]:
    """
    Fetch media from a URL into memory.

    For Twilio media URLs, uses HTTP Basic Auth with Account SID and Auth Token.

    Args:
        url: URL to fetch from

    Returns:
        Media bytes, or None if fetch fails
    """
    try:
        import requests
        from requests.auth import HTTPBasicAuth

        print(f"📥 Fetching media from: {url}")

        # Check if this is a Twilio media URL
        auth = None
        if "api.twilio.com" in url:
            # Get Twilio credentials from environment
            account_sid = config.TWILIO_ACCOUNT_SID
            auth_token = config.TWILIO_AUTH_TOKEN

            if account_sid and auth_token:
                auth = HTTPBasicAuth(account_sid, auth_token)
                print(f"🔐 Using Twilio authentication")
            else:
                print(f"⚠️  Warning: Twilio credentials not found in environment")

        response = requests.get(url, auth=auth, timeout=30)

        if response.status_code != 200:
            print(f"❌ Fetch failed with status {response.status_code}")
            if response.status_code == 401:
                print(f"❌ Authentication failed - check TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN")
            return None

        content = response.content
        print(f"✅ Fetched {len(content)} bytes")
        return content

    except Exception as e:
        print(f"❌ Error fetching media: {e}")
        import traceback
        traceback.print_exc()
        return None
