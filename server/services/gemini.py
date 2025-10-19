"""Gemini AI tools: text, image, and video analysis for 311 requests."""
import json
import re
import asyncio
import base64
import io
from typing import Optional, Dict, Any, Union
from pathlib import Path

import PIL.Image
import google.generativeai as genai
from google import genai as genai_live
from google.genai import types

from server.config import config

# Configure Gemini
genai.configure(api_key=config.GEMINI_API_KEY)


class GeminiModels:
    """Available models."""
    FLASH = 'gemini-2.5-flash'
    PRO = 'gemini-2.5-pro'
    FLASH_LITE = 'gemini-2.5-flash-lite'
    LIVE_FLASH = 'models/gemini-2.0-flash-exp'


# Shared prompt for 311 analysis
PROMPT_TEMPLATE = """Analyze this {media_type} for a San Francisco 311 service request.

Extract:
- Request Type (e.g., Abandoned Vehicle, Pothole, Graffiti, Streetlight Repair, Illegal Dumping)
- Location (full address in San Francisco)
- Details
- Confidence (0.00 to 1.00)

{content}

Return ONLY valid JSON:
{{"requestType": "...", "location": "...", "details": "...", "confidence": 0.XX}}"""


def _parse_response(text: str) -> Optional[Dict[str, Any]]:
    """Parse and validate JSON from Gemini response."""
    try:
        json_match = re.search(r'\{[\s\S]*\}', text)
        if not json_match:
            return None

        data = json.loads(json_match.group(0))

        if not all(k in data for k in ['requestType', 'location', 'confidence']):
            return None

        return data
    except:
        return None


async def analyze_text(message: str, model: str = GeminiModels.FLASH) -> Optional[Dict[str, Any]]:
    """Analyze text message."""
    try:
        print(f'🤖 [TEXT] {model}')

        prompt = PROMPT_TEMPLATE.format(
            media_type="text message",
            content=f'Message: "{message}"'
        )

        response = genai.GenerativeModel(model).generate_content(prompt)
        return _parse_response(response.text)
    except Exception as e:
        print(f'❌ [TEXT] {e}')
        return None


async def analyze_image(
    image_data: Union[bytes, str, Path],
    text: Optional[str] = None,
    model: str = GeminiModels.FLASH
) -> Optional[Dict[str, Any]]:
    """Analyze image (with optional text)."""
    try:
        print(f'🖼️ [IMAGE] {model}')

        # Load image
        if isinstance(image_data, (str, Path)):
            img = PIL.Image.open(image_data)
        else:
            img = PIL.Image.open(io.BytesIO(image_data))

        content = f'Image{f" with message: {text}" if text else ""}'
        prompt = PROMPT_TEMPLATE.format(media_type="image", content=content)

        response = genai.GenerativeModel(model).generate_content([prompt, img])
        return _parse_response(response.text)
    except Exception as e:
        print(f'❌ [IMAGE] {e}')
        return None


async def analyze_video(
    video_path: Union[str, Path],
    model: str = GeminiModels.LIVE_FLASH,
    max_duration: float = 10.0
) -> Optional[Dict[str, Any]]:
    """Analyze video using Gemini Live API."""
    try:
        from moviepy import VideoFileClip
        import numpy as np
    except ImportError:
        print('❌ [VIDEO] Install: pip install moviepy pillow numpy')
        return None

    try:
        print(f'🎥 [VIDEO] {video_path}')
        clip = VideoFileClip(str(video_path))

        client = genai_live.Client(
            http_options={"api_version": "v1beta"},
            api_key=config.GEMINI_API_KEY
        )

        config_live = types.LiveConnectConfig(
            response_modalities=["TEXT"],
            media_resolution="MEDIA_RESOLUTION_MEDIUM",
            system_instruction=types.Content(
                parts=[types.Part(text=PROMPT_TEMPLATE.format(
                    media_type="video",
                    content="Analyze video frames and audio"
                ))]
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
            result = _parse_response(''.join(full_text))

        async with client.aio.live.connect(model=model, config=config_live) as session:
            async with asyncio.TaskGroup() as tg:
                tg.create_task(send_frames())
                tg.create_task(send_audio())
                tg.create_task(send_to_session(session))
                tg.create_task(receive(session))

        clip.close()
        return result

    except Exception as e:
        print(f'❌ [VIDEO] {e}')
        return None
