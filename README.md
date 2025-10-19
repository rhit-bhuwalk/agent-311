<div align="center">
<img width="1200" height="475" alt="GHBanner" src="https://github.com/user-attachments/assets/0aa67016-6eaf-458a-adb2-6e31a0763ed6" />
</div>

# SF 311 WhatsApp Bot Dashboard

A full-stack application that demonstrates an AI-powered WhatsApp bot for submitting San Francisco 311 service requests. The system uses Twilio for WhatsApp messaging and Gemini AI for intelligent message analysis.

View your app in AI Studio: https://ai.studio/apps/drive/13ZxrTpztNKibK7zwxXn9Joto0oFEonoB

## Features

- 🤖 **AI-Powered Analysis**: Gemini AI analyzes WhatsApp messages to extract service request details
- 📱 **WhatsApp Integration**: Receive and respond to messages via Twilio WhatsApp
- 📊 **Real-time Dashboard**: React-based dashboard showing message processing and request status
- 🏙️ **311 Service Requests**: Automated submission of various SF 311 request types (potholes, graffiti, abandoned vehicles, etc.)

## Quick Start

**Prerequisites:**
- Node.js 18+
- Python 3.9+

1. **Install dependencies:**
   ```bash
   npm run install:all
   ```
   This installs both frontend (npm) and backend (Python) dependencies.

2. **Set up environment variables:**

   Create a `.env.local` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   PORT=3001
   ```

   Get your Gemini API key from: https://aistudio.google.com/app/apikey

3. **Run the application:**

   **Both frontend and backend (recommended):**
   ```bash
   npm run dev
   ```
   - Frontend runs on http://localhost:3000
   - Backend runs on http://localhost:3001

   **Frontend only (dashboard with mock data):**
   ```bash
   npm run dev:frontend
   ```

   **Backend only (Twilio webhook server):**
   ```bash
   npm run dev:server
   ```

## Twilio WhatsApp Setup

To connect the backend to Twilio WhatsApp:

1. **Expose your local server to the internet:**
   ```bash
   ngrok http 3001
   ```

2. **Configure Twilio Sandbox:**

   Go to [Twilio WhatsApp Sandbox Settings](https://console.twilio.com/us1/develop/sms/settings/whatsapp-sandbox)

   **When a message comes in:**
   - URL: `https://your-ngrok-url.ngrok.io/twilio/webhook`
   - Method: `POST`

   **Status callback URL (optional):**
   - URL: `https://your-ngrok-url.ngrok.io/twilio/status`
   - Method: `POST`

3. **Test the bot:**

   Send a message to your Twilio WhatsApp number:
   ```
   There's a pothole on Market Street near 5th. It's dangerous for bikes.
   ```

## Project Structure

```
.
├── frontend/            # React/Vite frontend application
│   ├── components/      # React components for dashboard
│   │   ├── Header.tsx
│   │   ├── MessageFeed.tsx
│   │   ├── MessageDetail.tsx
│   │   └── RequestStatus.tsx
│   ├── App.tsx          # Main React app
│   ├── types.ts         # TypeScript types
│   ├── constants.ts     # Mock data for dashboard
│   └── package.json     # Frontend dependencies
├── server/              # Python/FastAPI backend server
│   ├── main.py          # FastAPI app entry point
│   ├── config.py        # Configuration
│   ├── storage.py       # In-memory storage
│   ├── routes/          # API routes
│   │   └── twilio_webhook.py
│   ├── services/        # Business logic
│   │   ├── gemini.py    # Gemini AI integration
│   │   └── dedalus_service.py  # Dedalus AI + SF 311 form submission
│   └── requirements.txt # Python dependencies
├── graffiti-automation/ # Node.js service for SF 311 form automation
│   ├── src/             # Core automation logic
│   │   ├── server.js           # Express server
│   │   ├── form-filler.js      # Playwright form automation
│   │   ├── gemini-service.js   # AI field mapping
│   │   └── location-handler.js # Address geocoding
│   ├── test-cases/      # Comprehensive test suite (14 tests)
│   └── README.md        # Detailed documentation
├── .env.local           # Environment variables (create this)
└── package.json         # Root scripts for running both services
```

## Graffiti Form Automation

The `graffiti-automation/` directory contains a Node.js microservice that handles automated SF 311 graffiti form submissions using Playwright browser automation and Gemini AI.

### Features
- Automated multi-page form navigation with intelligent field detection
- AI-powered form field mapping from natural language descriptions
- Enhanced dropdown selection with proper form validation triggering
- Image upload support
- Address geocoding and auto-completion
- 14 comprehensive test cases covering diverse scenarios

### Running the Graffiti Automation Service

```bash
cd graffiti-automation
npm install
npm start
```

The service runs on `http://localhost:3000` and is automatically called by the Python backend's `dedalus_service.py` when submitting SF 311 forms.

See [graffiti-automation/README.md](graffiti-automation/README.md) for detailed documentation.

## Documentation

See [CLAUDE.md](CLAUDE.md) for detailed architecture documentation and [server/README.md](server/README.md) for backend-specific setup.

## Tech Stack

**Frontend:**
- React 19.2.0
- TypeScript
- Vite
- Tailwind CSS

**Backend:**
- Python 3.9+
- FastAPI
- Google Generative AI (Gemini)
- Twilio

## Current Status

- ✅ **Frontend Dashboard**: Fully functional with mock data (React/Vite)
- ✅ **Backend API**: Python/FastAPI server with auto-generated docs at `/docs`
- ✅ **Twilio Integration**: Receives and responds to WhatsApp messages
- ✅ **Gemini AI Analysis**: Extracts request details from natural language
- ✅ **SF 311 Graffiti Submission**: Fully automated using Playwright browser automation (graffiti-automation service)

## Production Deployment

For production deployment, consider:
- Deploying backend to Railway, Render, or similar platform
- Deploying frontend to Vercel, Netlify, or similar platform
- Deploying graffiti-automation service separately or as part of backend
- Update `GRAFFITI_API_URL` environment variable to point to deployed service
- Setting up proper Twilio account (not sandbox)
- Adding authentication and rate limiting
- Implementing additional SF 311 form types (potholes, street cleaning, etc.)
