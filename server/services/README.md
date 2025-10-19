# Gemini Tools - Simple 311 Analysis

Three simple tools for analyzing 311 requests from different media types.

## The Tools

```python
from server.services.gemini import analyze_text, analyze_image, analyze_video

# Text
result = await analyze_text("Pothole on Market St")

# Image
result = await analyze_image("photo.jpg", text="Optional text")
# or: analyze_image(image_bytes)

# Video
result = await analyze_video("video.mp4", max_duration=10.0)
```

All return the same format:
```json
{
  "requestType": "Pothole or Street Defect",
  "location": "Market St, San Francisco",
  "details": "...",
  "confidence": 0.95
}
```

## Installation

```bash
pip install -r ../requirements.txt
```

## Key Differences

- **Text & Image**: Standard Gemini API (fast, simple request/response)
- **Video**: Gemini Live API (streaming, processes frames + audio)

## Twilio Integration

```python
from server.services.gemini import analyze_text, analyze_image, analyze_video

# In your webhook:
if NumMedia > 0:
    if MediaContentType0.startswith('image/'):
        analysis = await analyze_image(downloaded_image, text=Body)
    elif MediaContentType0.startswith('video/'):
        analysis = await analyze_video(downloaded_video_path)
else:
    analysis = await analyze_text(Body)
```

That's it!
