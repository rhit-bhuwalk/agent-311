# Testing Twilio WhatsApp Integration

This guide will help you test the Twilio WhatsApp connection **before** adding Gemini AI complexity.

## Step 1: Start the Backend Server

```bash
# From project root
npm run dev:server

# Or directly
python -m uvicorn server.main:app --reload --port 3001
```

You should see:
```
✅ Configuration loaded successfully
INFO:     Uvicorn running on http://0.0.0.0:3001
```

## Step 2: Expose Your Local Server with ngrok

Install ngrok if you haven't already:
```bash
# macOS
brew install ngrok

# Or download from https://ngrok.com/download
```

Start ngrok to expose port 3001:
```bash
ngrok http 3001
```

You'll see output like:
```
Forwarding   https://abc123.ngrok.io -> http://localhost:3001
```

**Copy the HTTPS URL** (e.g., `https://abc123.ngrok.io`) - you'll need this for Twilio.

⚠️ **Important**: Keep ngrok running! If you restart it, the URL will change and you'll need to update Twilio.

## Step 3: Configure Twilio WhatsApp Sandbox

1. **Go to Twilio Console**:
   - Visit: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox
   - Login if needed

2. **Join the Sandbox** (if you haven't already):
   - Follow the instructions to send the join code to the Twilio WhatsApp number
   - Example: Send `join <your-code>` to +1 415 123 4567

3. **Configure the Webhook**:

   In the "Sandbox Configuration" section:

   **When a message comes in:**
   - URL: `https://your-ngrok-url.ngrok.io/twilio/test`
   - Method: `POST`

   Example: `https://abc123.ngrok.io/twilio/test`

   ⚠️ Note the `/twilio/test` at the end - this is our test endpoint!

4. **Save** the configuration

## Step 4: Test the Connection

1. **Send a WhatsApp message** to your Twilio sandbox number:
   ```
   Hello, testing the bot!
   ```

2. **Check your backend terminal** - you should see:
   ```
   ============================================================
   📱 TWILIO TEST WEBHOOK TRIGGERED!
   From: whatsapp:+14155551234
   Message: Hello, testing the bot!
   MessageSid: SM1234567890abcdef
   ============================================================
   ```

3. **Check WhatsApp** - you should receive a reply:
   ```
   ✅ Test successful! I received your message:

   "Hello, testing the bot!"

   From: whatsapp:+14155551234
   Message ID: SM1234567890abcdef
   ```

## Step 5: Verify Everything Works

Send a few more test messages with different content:

**Test 1: Simple message**
```
Test 123
```

**Test 2: Longer message**
```
There's a pothole on Market Street near 5th Avenue. It's pretty big.
```

**Test 3: Emoji test**
```
🚗 Testing emojis! 🎉
```

Each time:
- ✅ Backend terminal should show the incoming message
- ✅ WhatsApp should echo back your message

## Troubleshooting

### Not receiving messages in backend?

1. **Check ngrok is running**:
   ```bash
   curl https://your-ngrok-url.ngrok.io/health
   ```
   Should return: `{"status":"ok","timestamp":"..."}`

2. **Check Twilio webhook URL**:
   - Make sure it ends with `/twilio/test`
   - Make sure it's HTTPS (not HTTP)
   - Make sure the ngrok URL hasn't changed

3. **Check Twilio debugger**:
   - Go to: https://console.twilio.com/us1/monitor/logs/debugger
   - Look for recent webhook errors

### Not receiving replies in WhatsApp?

1. **Check backend logs** for errors
2. **Make sure you joined the sandbox** (send the join code first)
3. **Check Twilio account status** (trial accounts have limitations)

### ngrok URL keeps changing?

- Free ngrok URLs change every time you restart
- Either keep ngrok running, or sign up for a free ngrok account to get a static URL

## Next Steps

Once the test endpoint works perfectly:

1. **Switch to the full webhook** that includes Gemini AI:
   - Change Twilio URL from `/twilio/test` to `/twilio/webhook`
   - Make sure you have `GEMINI_API_KEY` in your `.env.local`
   - Test with a real 311 request like:
     ```
     There's a pothole on Market Street near 5th
     ```

2. **The full webhook will**:
   - Analyze the message with Gemini AI
   - Extract request type, location, and details
   - Simulate submitting to SF 311
   - Send back a confirmation with a case ID

## Test Endpoint vs. Full Webhook

| Endpoint | URL | What it does |
|----------|-----|--------------|
| **Test** | `/twilio/test` | Just echoes your message back - no AI |
| **Full** | `/twilio/webhook` | Full flow: Gemini AI → SF 311 → Reply |

Start with `/twilio/test` to verify Twilio works, then switch to `/twilio/webhook` for the full experience!
