"""Twilio webhook routes for handling incoming WhatsApp messages."""
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Form, Response, Depends
from twilio.twiml.messaging_response import MessagingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    from server.services.gemini import analyze_image, analyze_video, fetch_media_bytes, analyze_conversation
    from server.database import get_db, User, Message, get_recent_messages
except ModuleNotFoundError:
    from services.gemini import analyze_image, analyze_video, fetch_media_bytes, analyze_conversation
    from database import get_db, User, Message, get_recent_messages

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
    content_type: str,
    is_from_user: bool = True
) -> Message:
    """Store a message in the database."""
    message = Message(
        user_id=user.id,
        content=content,
        content_type=content_type,
        is_from_user=is_from_user
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
            print(f"❌ Failed to fetch media bytes from {media_url}")
            return None

        # Analyze based on type
        if media_type.startswith("image/"):
            print(f"🖼️  Analyzing image with Gemini...")
            analysis = await analyze_image(media_bytes, text=text_context)
            if analysis:
                content = f"<image>{analysis}</image>"
                print(f"💾 Storing image analysis: {analysis[:100]}...")
                message = await store_message(db, user, content, "image", is_from_user=True)
                print(f"✅ Stored image analysis")
                return message
            else:
                print(f"❌ Gemini analysis returned None")
                return None

        elif media_type.startswith("video/"):
            print(f"🎥 Analyzing video with Gemini...")
            analysis = await analyze_video(media_bytes)
            if analysis:
                content = f"<video>{analysis}</video>"
                print(f"💾 Storing video analysis: {analysis[:100]}...")
                message = await store_message(db, user, content, "video", is_from_user=True)
                print(f"✅ Stored video analysis")
                return message
            else:
                print(f"❌ Gemini video analysis returned None")
                return None
        else:
            print(f"❌ Unsupported media type: {media_type}")
            return None

    except Exception as e:
        print(f"❌ Error processing media: {e}")
        import traceback
        traceback.print_exc()
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

    Conversational flow:
    1. Store user's message (text/image/video)
    2. Get last 10 messages
    3. Analyze conversation with Gemini to extract reporting + location
    4. Ask for clarification if needed, or confirm if all info is present
    5. Store AI response
    """
    try:
        print(f'📨 Incoming message from {From}')
        print(f'📊 NumMedia: {NumMedia}, Body: "{Body}"')
        if NumMedia > 0:
            print(f'📎 MediaUrl0: {MediaUrl0}')
            print(f'📎 MediaContentType0: {MediaContentType0}')

        # Get or create user
        user = await get_or_create_user(db, From)

        # Store text message if present
        if Body and Body.strip():
            await store_message(db, user, Body, "text", is_from_user=True)
            print(f"✅ Stored text message from user")

        # Process media if present (images and videos get analyzed by Gemini)
        if NumMedia > 0 and MediaUrl0:
            print(f"🔄 Starting media processing...")
            result = await process_and_store_media(
                db=db,
                user=user,
                media_url=MediaUrl0,
                media_type=MediaContentType0 or "application/octet-stream",
                text_context=Body if Body and Body.strip() else None
            )
            if result:
                print(f"✅ Media processed successfully: {result.id}")
            else:
                print(f"❌ Media processing returned None")

        # Get last 10 messages for conversation context
        recent_messages = await get_recent_messages(db, user.id, limit=10)
        print(f"📜 Retrieved {len(recent_messages)} recent messages")

        # Convert messages to dict format for Gemini
        message_dicts = [
            {
                "content": msg.content,
                "is_from_user": msg.is_from_user,
                "content_type": msg.content_type
            }
            for msg in recent_messages
        ]

        # Analyze conversation with Gemini
        print(f"🤖 Analyzing conversation with Gemini...")
        analysis = await analyze_conversation(message_dicts)

        # Get the response message
        response_text = analysis.get("response_message", "I'm here to help you report issues to SF 311!")

        # Store AI response
        await store_message(db, user, response_text, "text", is_from_user=False)

        # Send response via Twilio
        twiml = MessagingResponse()
        twiml.message(response_text)

        return Response(content=str(twiml), media_type='text/xml')

    except Exception as error:
        print(f'❌ Error processing webhook: {error}')
        import traceback
        traceback.print_exc()

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
