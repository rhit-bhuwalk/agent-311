"""Twilio webhook routes for handling incoming WhatsApp messages."""
from datetime import datetime
from typing import Dict
from fastapi import APIRouter, Form, Response
from twilio.twiml.messaging_response import MessagingResponse

from server.services.gemini import analyze_text
from server.storage import add_message, add_request

router = APIRouter(prefix='/twilio', tags=['twilio'])


@router.post('/test')
async def twilio_test_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)):
    twiml = MessagingResponse()
    twiml.message(
        f"✅ Test successful! I received your message:\n\n"
        f'"{Body}"\n\n'
        f"From: {From}\n"
        f"Message ID: {MessageSid}"
    )

    return Response(content=str(twiml), media_type='text/xml')


@router.post('/webhook')
async def twilio_webhook(
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(...)
):
    try:
        print(f'📨 Incoming message from {From}: {Body}')

        # Create Twilio response
        twiml = MessagingResponse()

        # Analyze the message with Gemini using the currently selected model
        # Import here to avoid circular dependency
        from server.main import current_model
        analysis = await analyze_text(Body, current_model)

        if not analysis:
            twiml.message(
                'Sorry, I could not understand your request. '
                'Please provide more details about the issue, including the location.'
            )
            return Response(content=str(twiml), media_type='text/xml')

        print('🤖 Gemini Analysis:', analysis)

        # If confidence is too low, ask for clarification
        if analysis['confidence'] < 0.7:
            twiml.message(
                f"I think you're reporting: {analysis['requestType']} "
                f"at {analysis['location']}. "
                f"However, I'm not very confident. Could you provide more details?"
            )
            return Response(content=str(twiml), media_type='text/xml')

        # Submit to SF 311
        result = None
        request_status = 'Pending'
        sf311_case_id = None

        try:
            result = await submit_to_311(analysis, From, MessageSid)

            if result['success']:
                request_status = 'Submitted'
                sf311_case_id = result['caseId']

                twiml.message(
                    f"✅ Your {analysis['requestType']} report has been submitted to SF 311!\n\n"
                    f"📍 Location: {analysis['location']}\n"
                    f"📋 Case ID: {result['caseId']}\n\n"
                    f"You can track your request at: {result.get('trackingUrl', 'https://www.sf.gov/check-status-311-request')}"
                )
            else:
                request_status = 'Failed'

                twiml.message(
                    f"⚠️ I understood your request but couldn't submit it automatically.\n\n"
                    f"📍 {analysis['requestType']} at {analysis['location']}\n\n"
                    f"Please submit manually at: https://www.sf.gov/topics/311-online-services\n"
                    f"Reason: {result.get('error', 'Unknown error')}"
                )

        except Exception as submit_error:
            print(f'❌ Error submitting to 311: {submit_error}')
            request_status = 'Failed'

            twiml.message(
                f"⚠️ I understood your request:\n\n"
                f"📍 {analysis['requestType']} at {analysis['location']}\n\n"
                f"But there was an error submitting. Please try submitting manually at:\n"
                f"https://www.sf.gov/topics/311-online-services"
            )

        # Store the message and request in memory
        message = {
            'id': MessageSid,
            'from': From,
            'timestamp': datetime.now().isoformat(),
            'text': Body,
            'analysis': analysis,
            'automationLog': result.get('automationLog', []) if result else []
        }

        request = {
            'id': f'req_{int(datetime.now().timestamp() * 1000)}',
            'messageId': MessageSid,
            'requestType': analysis['requestType'],
            'status': request_status,
            'submittedAt': datetime.now().isoformat(),
            'sf311CaseId': sf311_case_id
        }

        add_message(message)
        add_request(request)

        print('💾 Stored message and request in memory')

        return Response(content=str(twiml), media_type='text/xml')

    except Exception as error:
        print(f'❌ Error processing webhook: {error}')

        twiml = MessagingResponse()
        twiml.message(
            'Sorry, there was an error processing your request. '
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
