"""Dedalus AI service for conversation analysis."""
import asyncio
import json
import os
from typing import Optional
import requests

from dedalus_labs import AsyncDedalus, DedalusRunner

try:
    from server.config import config
except ModuleNotFoundError:
    from config import config


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
    try:
        print(f"🔧 Tool called: submit_sf311_form")
        print(f"   form_url: {form_url}")
        print(f"   description: {description}")
        print(f"   image_base64: {'Yes (' + str(len(image_base64)) + ' chars)' if image_base64 else 'No'}")

        api_url = "https://a6b437402ddb.ngrok-free.app/api/submit"
        payload = {
            "formUrl": form_url,
            "description": description
        }

        # Add image if provided
        if image_base64:
            payload["imageBase64"] = image_base64

        response = requests.post(
            api_url,
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

        # Create the prompt for Dedalus
        prompt = f"""You are a helpful assistant for SF 311 service requests. Your job is to understand what issue the user is reporting and where it's located.

You have access to a tool called `submit_sf311_form` that can submit SF 311 requests.

IMPORTANT: When BOTH the issue type and location are clear and complete, you MUST use the `submit_sf311_form` tool to submit the request.

Form URLs for different issue types:
- Graffiti: https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti
- Pothole: https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_pothole
- Illegal dumping: https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_illegaldumping

Analyze the following conversation and extract:
1. **reporting**: What is being reported (e.g., "broken pothole", "graffiti", "illegal dumping")
2. **location**: Where is it located (full address if possible, e.g., "1160 Mission Street, San Francisco")

If BOTH reporting and location are clear:
- Use the submit_sf311_form tool with the appropriate form URL and a description combining the issue and location
- Set needs_clarification to false
- Provide a confirmation message

If EITHER is unclear or missing:
- Set needs_clarification to true
- Ask specifically for what's missing

CONVERSATION HISTORY:
{conversation_text}

After analyzing (and submitting if appropriate), respond with ONLY valid JSON in this exact format:
{{
    "reporting": "what is being reported or null if unclear",
    "location": "where it is located or null if unclear",
    "needs_clarification": true/false,
    "clarification_question": "question to ask if needs_clarification is true, otherwise null",
    "response_message": "friendly message to send to the user"
}}

Examples:

If user says "there's a pothole on mission street":
{{
    "reporting": "pothole",
    "location": "Mission Street",
    "needs_clarification": true,
    "clarification_question": "Can you provide the exact address or cross streets for the pothole on Mission Street?",
    "response_message": "I understand there's a pothole on Mission Street. Can you provide the exact address or cross streets so I can submit this to SF 311?"
}}

If user says "broken pothole at 1160 mission street":
 respond with:
{{
    "reporting": "pothole",
    "location": "1160 Mission Street",
    "needs_clarification": false,
    "clarification_question": null,
    "response_message": "Perfect! I've submitted your report for a pothole at 1160 Mission Street to SF 311. You should receive a case number shortly."
}}
then call the submit_sf311_form tool with the appropriate form URL and description"""

        # Add image context if available
        if latest_image_base64:
            prompt += """

IMPORTANT: An image is available in the conversation. When you call submit_sf311_form, the image will be automatically included.
"""

        prompt += """

Now analyze the conversation above, use tools if appropriate, and respond with JSON only:"""

        # Initialize Dedalus client and runner
        client = AsyncDedalus()
        runner = DedalusRunner(client)

        # Create a wrapper function that includes the image
        def submit_with_image(form_url: str, description: str) -> str:
            """Submit SF311 form with image if available."""
            return submit_sf311_form(form_url, description, latest_image_base64 or "")

        # Run the analysis using Dedalus with GPT-5 and the SF311 submission tool
        print(f"🤖 Analyzing conversation with Dedalus (with SF311 submission tool)...")
        print(f"📸 Image available: {bool(latest_image_base64)}")
        if latest_image_base64:
            print(f"📸 Image size: {len(latest_image_base64)} chars")

        print(f"🔑 DEDALUS_API_KEY set: {bool(config.DEDALUS_API_KEY)}")
        print(f"🔑 DEDALUS_API_KEY length: {len(config.DEDALUS_API_KEY) if config.DEDALUS_API_KEY else 0}")

        try:
            print(f"📞 Starting Dedalus runner.run()...")
            import asyncio
            response = await asyncio.wait_for(
                runner.run(
                    input=prompt,
                    model="openai/gpt-5",
                    tools=[submit_with_image]
                ),
                timeout=60.0  # Increased to 60 second timeout
            )

            print(f"✅ Dedalus runner completed successfully")
            result_text = response.final_output.strip()
            print(f"📝 Dedalus raw response: {result_text[:200]}...")
        except asyncio.TimeoutError:
            print(f"❌ Dedalus timed out after 60 seconds")
            print(f"⚠️  This may indicate: API key issues, model issues, or network problems")
            # Return a fallback response
            return {
                "reporting": None,
                "location": None,
                "needs_clarification": True,
                "clarification_question": "I'm having trouble processing your request. Can you describe what issue you'd like to report?",
                "response_message": "I'm having trouble processing your request. Can you describe what issue you'd like to report and where it's located?"
            }
        except Exception as e:
            print(f"❌ Dedalus runner error: {type(e).__name__}: {e}")
            import traceback
            print(f"📋 Full traceback:")
            traceback.print_exc()
            # Return fallback instead of crashing
            return {
                "reporting": None,
                "location": None,
                "needs_clarification": True,
                "clarification_question": "I encountered an error. Can you describe what you'd like to report?",
                "response_message": "I encountered an error processing your message. Can you tell me what issue you'd like to report and where it's located?"
            }

        # Try to extract JSON from response
        # Sometimes the model wraps it in ```json blocks
        if "```json" in result_text:
            result_text = result_text.split("```json")[1].split("```")[0].strip()
        elif "```" in result_text:
            result_text = result_text.split("```")[1].split("```")[0].strip()

        result = json.loads(result_text)
        print(f"💬 Dedalus conversation analysis: {result}")
        return result

    except Exception as e:
        print(f"❌ Error in analyze_conversation_with_dedalus: {e}")
        import traceback
        traceback.print_exc()
        # Return a fallback response
        return {
            "reporting": None,
            "location": None,
            "needs_clarification": True,
            "clarification_question": "I'm having trouble understanding. Can you describe what issue you'd like to report and where it's located?",
            "response_message": "I'm having trouble understanding. Can you describe what issue you'd like to report and where it's located?"
        }
