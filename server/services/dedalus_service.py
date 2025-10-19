"""Dedalus AI service for conversation analysis."""
import asyncio
import json
import os
import traceback
from typing import Optional

import requests
from dedalus_labs import AsyncDedalus, DedalusRunner

try:
    from server.config import config
    from server.services.prompts import get_dedalus_analysis_prompt
except ModuleNotFoundError:
    from config import config
    from services.prompts import get_dedalus_analysis_prompt


# Constants
SF311_API_URL = "https://a6b437402ddb.ngrok-free.app/api/submit"
DEDALUS_TIMEOUT_SECONDS = 60


def submit_sf311_form(form_url: str, description: str, image_base64: str = "") -> str:
    """
    Submit a SF 311 service request form.

    Args:
        form_url: The SF 311 form URL (e.g., "https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti")
        description: Description of the issue including location and details
        image_base64: Base64 encoded image data (optional)

    Returns:
        JSON string with submission result
    """
    print(f"🔧 Tool called: submit_sf311_form")
    print(f"   form_url: {form_url}")
    print(f"   description: {description}")
    print(f"   image_base64: {'Yes (' + str(len(image_base64)) + ' chars)' if image_base64 else 'No'}")

    try:
        payload = {
            "formUrl": form_url,
            "description": description
        }

        # Add image if provided
        if image_base64:
            payload["imageBase64"] = image_base64

        response = requests.post(
            SF311_API_URL,
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=30
        )

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Form submitted successfully: {result}")
            return json.dumps(result)
        else:
            error_msg = f"Form submission failed with status {response.status_code}: {response.text}"
            print(f"❌ {error_msg}")
            return json.dumps({"error": error_msg})

    except Exception as e:
        error_msg = f"Error submitting form: {str(e)}"
        print(f"❌ {error_msg}")
        return json.dumps({"error": error_msg})


def _build_conversation_and_extract_image(messages: list[dict]) -> tuple[str, Optional[str]]:
    """
    Build conversation history and extract the most recent image.

    Args:
        messages: List of message dicts

    Returns:
        Tuple of (conversation_text, latest_image_base64)
    """
    conversation = []
    latest_image_base64 = None

    for msg in messages:
        role = "user" if msg.get("is_from_user") else "assistant"
        content = msg.get("content", "")
        conversation.append(f"{role.upper()}: {content}")

        # Keep track of the latest image from user
        if msg.get("is_from_user") and msg.get("image_data"):
            latest_image_base64 = msg.get("image_data")
            print(f"📸 Found image in conversation ({len(latest_image_base64)} chars)")

    conversation_text = "\n".join(conversation)
    return conversation_text, latest_image_base64


def _extract_json_from_response(result_text: str) -> str:
    """
    Extract JSON from response text, handling markdown code blocks.

    Args:
        result_text: The raw response text

    Returns:
        Cleaned JSON string
    """
    # Sometimes the model wraps it in ```json blocks
    if "```json" in result_text:
        return result_text.split("```json")[1].split("```")[0].strip()
    elif "```" in result_text:
        return result_text.split("```")[1].split("```")[0].strip()
    return result_text


def _get_fallback_response(message: str) -> dict:
    """
    Generate a fallback response when analysis fails.

    Args:
        message: The clarification message to send to user

    Returns:
        Fallback analysis dict
    """
    return {
        "reporting": None,
        "location": None,
        "needs_clarification": True,
        "clarification_question": message,
        "response_message": message
    }


def _log_analysis_details(image_base64: Optional[str]) -> None:
    """Log details about the Dedalus analysis being performed."""
    print(f"🤖 Analyzing conversation with Dedalus (with SF311 submission tool)...")
    print(f"📸 Image available: {bool(image_base64)}")
    if image_base64:
        print(f"📸 Image size: {len(image_base64)} chars")
    print(f"🔑 DEDALUS_API_KEY set: {bool(config.DEDALUS_API_KEY)}")
    print(f"🔑 DEDALUS_API_KEY length: {len(config.DEDALUS_API_KEY) if config.DEDALUS_API_KEY else 0}")


async def _run_dedalus_analysis(runner: DedalusRunner, prompt: str, submit_tool):
    """
    Run Dedalus analysis with timeout and error handling.

    Args:
        runner: The Dedalus runner instance
        prompt: The analysis prompt
        submit_tool: The SF311 submission tool function

    Returns:
        The response text from Dedalus (str) or fallback response dict on error
    """
    try:
        print(f"📞 Starting Dedalus runner.run()...")
        response = await asyncio.wait_for(
            runner.run(
                input=prompt,
                model="openai/gpt-5",
                tools=[submit_tool]
            ),
            timeout=DEDALUS_TIMEOUT_SECONDS
        )

        print(f"✅ Dedalus runner completed successfully")
        result_text = response.final_output.strip()
        print(f"📝 Dedalus raw response: {result_text[:200]}...")
        return result_text

    except asyncio.TimeoutError:
        print(f"❌ Dedalus timed out after {DEDALUS_TIMEOUT_SECONDS} seconds")
        print(f"⚠️  This may indicate: API key issues, model issues, or network problems")
        return _get_fallback_response(
            "I'm having trouble processing your request. Can you describe what issue you'd like to report and where it's located?"
        )

    except Exception as e:
        print(f"❌ Dedalus runner error: {type(e).__name__}: {e}")
        print(f"📋 Full traceback:")
        traceback.print_exc()
        return _get_fallback_response(
            "I encountered an error processing your message. Can you tell me what issue you'd like to report and where it's located?"
        )


async def analyze_conversation_with_dedalus(messages: list[dict]) -> dict:
    """
    Analyze conversation history using Dedalus to extract what's being reported and where.

    Args:
        messages: List of message dicts with 'content', 'is_from_user', and 'content_type'

    Returns:
        Dict with:
        - reporting: What is being reported (e.g., "broken pothole")
        - location: Where it's located (e.g., "1160 Mission Street")
        - needs_clarification: Boolean - true if more info needed
        - clarification_question: Question to ask user if needs_clarification is true
        - response_message: Message to send back to user
    """
    try:
        # Set the API key in the environment (Dedalus SDK reads from DEDALUS_API_KEY)
        os.environ['DEDALUS_API_KEY'] = config.DEDALUS_API_KEY

        # Build conversation history and extract the most recent image
        conversation_text, latest_image_base64 = _build_conversation_and_extract_image(messages)

        # Create the prompt for Dedalus
        prompt = get_dedalus_analysis_prompt(conversation_text, has_image=bool(latest_image_base64))

        # Initialize Dedalus client and runner
        client = AsyncDedalus()
        runner = DedalusRunner(client)

        # Create a wrapper function that includes the image
        def submit_with_image(form_url: str, description: str) -> str:
            """Submit SF311 form with image if available."""
            return submit_sf311_form(form_url, description, latest_image_base64 or "")

        # Log analysis details
        _log_analysis_details(latest_image_base64)

        # Run Dedalus analysis
        result_text = await _run_dedalus_analysis(runner, prompt, submit_with_image)

        # If we got a dict back (fallback response), return it
        if isinstance(result_text, dict):
            return result_text

        # Parse and return the result
        result_text = _extract_json_from_response(result_text)
        result = json.loads(result_text)
        print(f"💬 Dedalus conversation analysis: {result}")
        return result

    except Exception as e:
        print(f"❌ Error in analyze_conversation_with_dedalus: {e}")
        traceback.print_exc()
        return _get_fallback_response(
            "I'm having trouble understanding. Can you describe what issue you'd like to report and where it's located?"
        )
