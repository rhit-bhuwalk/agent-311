# Live WhatsApp Demo Setup Guide

## ✅ Completed Steps

- [x] Created `.env.local` configuration file
- [x] Installed all dependencies (frontend, backend, graffiti-automation)
- [x] Fixed port conflict (graffiti now runs on port 3002)
- [x] Created startup script

## 🔑 Step 1: Add Your API Keys

Edit `.env.local` and add your API keys:

```bash
# REQUIRED - Get from: https://aistudio.google.com/app/apikey
GEMINI_API_KEY=your_actual_gemini_api_key

# REQUIRED FOR WHATSAPP - Get from: https://console.twilio.com/
TWILIO_ACCOUNT_SID=your_actual_twilio_sid
TWILIO_AUTH_TOKEN=your_actual_twilio_token
```

**Where to get keys:**
- Gemini API: https://aistudio.google.com/app/apikey
- Twilio (free trial): https://console.twilio.com/

## 🚀 Step 2: Start All Services

### Option A: Use the startup script (recommended)
```bash
./start-demo.sh
```

This will automatically start:
- Frontend on http://localhost:3000
- Backend on http://localhost:3001
- Graffiti automation on http://localhost:3002

### Option B: Start services manually

**Terminal 1 - Backend:**
```bash
source .venv/bin/activate
python3 -m uvicorn server.main:app --reload --port 3001
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

**Terminal 3 - Graffiti Automation (optional):**
```bash
cd graffiti-automation
npm start
```

## 🌐 Step 3: Test the Dashboard

Visit http://localhost:3000 - you should see the dashboard with mock data.

Test the backend API at http://localhost:3001/docs (FastAPI auto-generated docs).

## 📱 Step 4: Set Up WhatsApp (For Live Demo)

### Install ngrok
```bash
# macOS
brew install ngrok

# Or download from: https://ngrok.com/download
```

### Start ngrok tunnel
```bash
ngrok http 3001
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:3001
```

Copy that `https://abc123.ngrok.io` URL.

### Configure Twilio WhatsApp Sandbox

1. Go to: https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox

2. Set webhook URLs:
   - **When a message comes in:**
     - URL: `https://abc123.ngrok.io/twilio/webhook`
     - Method: `POST`

   - **Status callback URL (optional):**
     - URL: `https://abc123.ngrok.io/twilio/status`
     - Method: `POST`

3. Join the WhatsApp sandbox:
   - Send the code shown (e.g., "join <your-code>") to the WhatsApp number

## 🧪 Step 5: Test End-to-End

Send a WhatsApp message to your Twilio sandbox number:

**Example messages:**

1. **Simple graffiti report:**
   ```
   There's graffiti at 1160 Mission Street with offensive language
   ```

2. **Report with image:**
   - Take a photo of graffiti
   - Send the photo with caption: "Graffiti on the bridge at 508 Golden Gate Ave"

3. **Multi-turn conversation:**
   ```
   User: There's a pothole
   Bot: Where is the pothole located?
   User: On Market Street near 5th
   Bot: [Submits request]
   ```

## 📊 Monitoring

### View logs:
```bash
# Backend logs
tail -f logs/backend.log

# Frontend logs
tail -f logs/frontend.log

# Graffiti automation logs
tail -f logs/graffiti.log
```

### Check ngrok requests:
Visit http://localhost:4040 to see the ngrok inspector.

### Check API endpoints:
Visit http://localhost:3001/docs for interactive API documentation.

## 🎯 Demo Script

### For judges/viewers:

1. **Show the dashboard** (http://localhost:3000)
   - Point out the WhatsApp message feed
   - Show the 311 request tracking
   - Highlight the AI analysis panel

2. **Send a live WhatsApp message**
   - Show your phone screen
   - Send: "There's graffiti at 1160 Mission Street with profanity"
   - Watch it appear in the dashboard in real-time

3. **Show the AI processing**
   - Point out Gemini's analysis in the message detail
   - Show location extraction
   - Show request type classification

4. **Show the automation**
   - Open the automation log
   - Show how it filled the SF 311 form
   - Show the case number generated

5. **Test with an image**
   - Send a photo via WhatsApp
   - Show how Gemini analyzes the image
   - Show it being attached to the form submission

## 🐛 Troubleshooting

### Port already in use
```bash
# Kill process on port 3000, 3001, or 3002
lsof -ti:3000 | xargs kill
lsof -ti:3001 | xargs kill
lsof -ti:3002 | xargs kill
```

### Services not starting
```bash
# Check logs
cat logs/backend.log
cat logs/frontend.log
cat logs/graffiti.log
```

### Twilio webhook not receiving messages
1. Check ngrok is running: `curl http://localhost:4040/api/tunnels`
2. Check webhook URL in Twilio console matches ngrok URL
3. Check backend logs for incoming requests

### Virtual environment issues
```bash
# Recreate venv if needed
python3 -m venv .venv
source .venv/bin/activate
pip install -r server/requirements.txt
```

## 🎬 Recording the Demo

### For video submission:

1. Start screen recording
2. Open http://localhost:3000
3. Show the dashboard
4. Switch to phone screen capture
5. Send WhatsApp message
6. Switch back to dashboard
7. Show the message processing
8. Show the form submission result

### Tools:
- macOS: QuickTime Player (File > New Screen Recording)
- Or: OBS Studio (free, powerful)
- Phone mirroring: QuickTime (iPhone) or scrcpy (Android)

## 📋 Checklist Before Demo

- [ ] All API keys configured in `.env.local`
- [ ] All services start without errors
- [ ] Dashboard loads at http://localhost:3000
- [ ] API docs accessible at http://localhost:3001/docs
- [ ] ngrok tunnel running
- [ ] Twilio webhook configured
- [ ] WhatsApp sandbox joined
- [ ] Test message works end-to-end
- [ ] Screen recording software ready

## 🎉 You're Ready!

Everything is set up. To start the demo:

```bash
./start-demo.sh
```

Then in another terminal:
```bash
ngrok http 3001
```

Good luck with your demo! 🚀
