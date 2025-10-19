"""Twilio webhook routes for handling incoming WhatsApp messages."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Form, Response, Depends
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    from server.services.gemini import analyze_image, analyze_video, fetch_media_bytes
    from server.database import get_db, User, Message
except ModuleNotFoundError:
    from services.gemini import analyze_image, analyze_video, fetch_media_bytes
    from database import get_db, User, Message

router = APIRouter(prefix='/twilio', tags=['twilio'])


async def get_or_create_user(db: AsyncSession, phone_number: str) -> User:
    """Get existing user or create a new one."""
    # Try to find existing user
    result = await db.execute(
        select(User).where(User.phone_number == phone_number)
    )
    user = result.scalar_one_or_none()

    if user is None:
        # Create new user
        user = User(phone_number=phone_number)
        db.add(user)
        await db.commit()
        await db.refresh(user)
        print(f"👤 Created new user: {phone_number}")

    return user


async def store_message(
    db: AsyncSession,
    user: User,
    content: str,
    content_type: str
) -> Message:
    """Store a message in the database."""
    message = Message(
        user_id=user.id,
        content=content,
        content_type=content_type
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)
    return message


async def process_and_store_media(
    db: AsyncSession,
    user: User,
    media_url: str,
    media_type: str,
    text_context: Optional[str] = None
) -> Optional[Message]:
    """
    Process media (image or video), analyze it with Gemini, and store description.

    Args:
        db: Database session
        user: User object
        media_url: URL to the media file
        media_type: MIME type of the media
        text_context: Optional text message sent with the media

    Returns:
        Message object if successful, None otherwise
    """
    try:
        print(f"📎 Processing {media_type}")

        # Fetch media bytes
        media_bytes = await fetch_media_bytes(media_url)
        if not media_bytes:
            return None

        # Analyze based on type
        if media_type.startswith("image/"):
            analysis = await analyze_image(media_bytes, text=text_context)
            if analysis:
                content = f"<image>{analysis}</image>"
                message = await store_message(db, user, content, "image")
                print(f"✅ Stored image analysis")
                return message

        elif media_type.startswith("video/"):
            analysis = await analyze_video(media_bytes)
            if analysis:
                content = f"<video>{analysis}</video>"
                message = await store_message(db, user, content, "video")
                print(f"✅ Stored video analysis")
                return message

    except Exception as e:
        print(f"❌ Error processing media: {e}")
        return None


@router.post('/webhook')
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(default=""),
    MessageSid: str = Form(...),
    NumMedia: int = Form(default=0),
    MediaUrl0: Optional[str] = Form(default=None),
    MediaContentType0: Optional[str] = Form(default=None),
    db: AsyncSession = Depends(get_db)
):
    """
    Main webhook endpoint for incoming WhatsApp messages.

    Handles:
    - Text messages: stored directly
    - Images: analyzed by Gemini, description stored with <image> tags
    - Videos: analyzed by Gemini, description stored with <video> tags
    """
    try:
        print(f'📨 Incoming message from {From}')

        # Get or create user
        user = await get_or_create_user(db, From)

        twiml = MessagingResponse()

        # Store text message if present
        if Body and Body.strip():
            await store_message(db, user, Body, "text")
            print(f"✅ Stored text message")

        # Process media if present (images and videos get analyzed by Gemini)
        if NumMedia > 0 and MediaUrl0:
            await process_and_store_media(
                db=db,
                user=user,
                media_url=MediaUrl0,
                media_type=MediaContentType0 or "application/octet-stream",
                text_context=Body if Body and Body.strip() else None
            )

        # Send acknowledgment
        if Body and Body.strip():
            twiml.message("✅ Got it! Message stored.")
        else:
            twiml.message("✅ Received and analyzed your media!")

        return Response(content=str(twiml), media_type='text/xml')

    except Exception as error:
        print(f'❌ Error processing webhook: {error}')

        twiml = MessagingResponse()
        twiml.message(
            'Sorry, there was an error processing your message. '
            'Please try again later.'
        )
        return Response(content=str(twiml), media_type='text/xml')


@router.post('/status')
async def twilio_status(
    MessageStatus: str = Form(...),
    MessageSid: str = Form(...)
):
    """
    Status callback endpoint (optional).

    Args:
        MessageStatus: Current status of the message
        MessageSid: Twilio message identifier
    """
    print(f'📊 Message {MessageSid} status: {MessageStatus}')
    return {'status': 'ok'}
