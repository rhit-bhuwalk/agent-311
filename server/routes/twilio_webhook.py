"""Twilio webhook routes for handling incoming WhatsApp messages."""
import base64
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Form, Response, Depends, BackgroundTasks
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

try:
    from server.services.gemini import analyze_image, analyze_video, fetch_media_bytes
    from server.services.dedalus_service import analyze_conversation_with_dedalus
    from server.database import get_db, User, Message, get_recent_messages, async_session_maker
    from server.config import config
except ModuleNotFoundError:
    from services.gemini import analyze_image, analyze_video, fetch_media_bytes
    from services.dedalus_service import analyze_conversation_with_dedalus
    from database import get_db, User, Message, get_recent_messages, async_session_maker
    from config import config

router = APIRouter(prefix='/twilio', tags=['twilio'])


def send_whatsapp_message(to: str, message: str):
    """Send a WhatsApp message via Twilio REST API."""
    try:
        client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)

        # Extract phone number from WhatsApp format (whatsapp:+1234567890 -> +1234567890)
        to_number = to.replace('whatsapp:', '')

        # Twilio WhatsApp numbers need the whatsapp: prefix
        message = client.messages.create(
            from_='whatsapp:+14155238886',  # Twilio Sandbox number
            body=message,
            to=f'whatsapp:{to_number}'
        )

        print(f"✅ Message sent via Twilio API: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"❌ Error sending WhatsApp message: {e}")
        import traceback
        traceback.print_exc()
        return None


async def process_message_background(user_id, phone_number: str):
    """Background task to process message and send response."""
    try:
        print(f"🔄 Background processing started for {phone_number}")

        # Create a new database session for the background task
        async with async_session_maker() as db:
            # Get last 10 messages for conversation context
            recent_messages = await get_recent_messages(db, user_id, limit=10)
            print(f"📜 Retrieved {len(recent_messages)} recent messages")

            # Convert messages to dict format for Dedalus (include image data)
            message_dicts = [
                {
                    "content": msg.content,
                    "is_from_user": msg.is_from_user,
                    "content_type": msg.content_type,
                    "image_data": msg.image_data if hasattr(msg, 'image_data') else None
                }
                for msg in recent_messages
            ]

            # Analyze conversation with Dedalus
            print(f"🤖 Analyzing conversation with Dedalus...")
            try:
                analysis = await analyze_conversation_with_dedalus(message_dicts)
                print(f"✅ Dedalus analysis completed: {analysis}")
            except Exception as e:
                print(f"❌ Error calling analyze_conversation_with_dedalus: {e}")
                import traceback
                traceback.print_exc()
                # Use fallback
                analysis = {
                    "reporting": None,
                    "location": None,
                    "needs_clarification": True,
                    "clarification_question": "I encountered an error. Can you describe what you'd like to report?",
                    "response_message": "I encountered an error processing your message. Can you tell me what issue you'd like to report and where it's located?"
                }

            # Get the response message
            response_text = analysis.get("response_message", "I'm here to help you report issues to SF 311!")
            print(f"📤 Sending response to user: {response_text}")

            # Store AI response in database
            message = Message(
                user_id=user_id,
                content=response_text,
                content_type="text",
                is_from_user=False,
                image_data=None
            )
            db.add(message)
            await db.commit()

            # Send response via Twilio API
            send_whatsapp_message(phone_number, response_text)

            print(f"✅ Background processing completed for {phone_number}")

    except Exception as e:
        print(f"❌ Error in background processing: {e}")
        import traceback
        traceback.print_exc()


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
    is_from_user: bool = True,
    image_data: Optional[str] = None
) -> Message:
    """Store a message in the database."""
    message = Message(
        user_id=user.id,
        content=content,
        content_type=content_type,
        is_from_user=is_from_user,
        image_data=image_data
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
                # Convert image bytes to base64
                image_base64 = base64.b64encode(media_bytes).decode('utf-8')
                print(f"💾 Storing image analysis: {analysis[:100]}...")
                print(f"📸 Storing image as base64 ({len(image_base64)} chars)")
                message = await store_message(
                    db, user, content, "image",
                    is_from_user=True,
                    image_data=image_base64
                )
                print(f"✅ Stored image analysis with base64 data")
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
    background_tasks: BackgroundTasks,
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

    This endpoint responds immediately to Twilio (within 15 seconds) and processes
    the message in the background to avoid timeout issues.

    Flow:
    1. Store user's message (text/image/video) immediately
    2. Return 200 OK to Twilio
    3. Process message analysis in background
    4. Send response via Twilio API when ready
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

        # Add background task to process message and send response
        background_tasks.add_task(process_message_background, user.id, From)
        print(f"⏰ Background task scheduled for {From}")

        # Return empty 200 OK immediately to Twilio
        return Response(content='', status_code=200)

    except Exception as error:
        print(f'❌ Error processing webhook: {error}')
        import traceback
        traceback.print_exc()

        # Still return 200 to Twilio to avoid retries
        return Response(content='', status_code=200)


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
