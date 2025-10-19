# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a React-based dashboard application that visualizes a conceptual WhatsApp bot for submitting SF 311 service requests. The bot is powered by Twilio and Gemini AI. This is a **frontend simulation** of the backend process - it displays mock data to demonstrate how the system would work in production.

AI Studio App: https://ai.studio/apps/drive/13ZxrTpztNKibK7zwxXn9Joto0oFEonoB

## Project Structure

```
.
├── frontend/          # React/Vite frontend application
├── server/           # Python/FastAPI backend server
├── .env.local        # Environment variables (create this)
└── package.json      # Root scripts for running both services
```

## Development Commands

**Install all dependencies:**
```bash
npm run install:all
```
This installs both frontend npm packages and Python server dependencies.

**Or install separately:**
```bash
# Frontend dependencies
npm run install:frontend

# Server dependencies
npm run install:server
# or: pip install -r server/requirements.txt
```

**Run both frontend and backend concurrently (recommended):**
```bash
npm run dev
```
This starts both the Vite dev server (port 3000) and FastAPI server (port 3001)

**Run frontend only:**
```bash
npm run dev:frontend
# or: cd frontend && npm run dev
```
Starts Vite dev server on http://localhost:3000

**Run backend server only:**
```bash
npm run dev:server
# or: python -m uvicorn server.main:app --reload --port 3001
```
Starts FastAPI server on http://localhost:3001

**Build for production:**
```bash
npm run build
```

## Environment Setup

Create a `.env.local` file **in the project root** and set your Gemini API key:
```
GEMINI_API_KEY=your_api_key_here
```

The Vite config ([frontend/vite.config.ts](frontend/vite.config.ts)) loads this from the parent directory and exposes it as both `process.env.API_KEY` and `process.env.GEMINI_API_KEY`.

## Frontend Architecture

### Data Flow
The app follows a unidirectional data flow pattern:
1. Mock data is defined in [frontend/constants.ts](frontend/constants.ts) (`MOCK_MESSAGES` and `MOCK_REQUESTS`)
2. [frontend/App.tsx](frontend/App.tsx) manages state and passes data down to child components
3. Components are presentational and receive data via props

### Component Structure

**Main App** ([frontend/App.tsx](frontend/App.tsx))
- Root component managing message and request state
- Uses a 3-column grid layout (1 column for message feed, 2 columns for details/status)
- Handles message selection state

**Components:**
- [frontend/components/Header.tsx](frontend/components/Header.tsx) - Title bar with "Simulation Mode" badge
- [frontend/components/MessageFeed.tsx](frontend/components/MessageFeed.tsx) - Scrollable list of incoming WhatsApp messages
- [frontend/components/MessageDetail.tsx](frontend/components/MessageDetail.tsx) - Shows selected message details including:
  - Original message text
  - Gemini AI analysis (request type, location, details, confidence)
  - Automation log showing the simulated submission process
- [frontend/components/RequestStatus.tsx](frontend/components/RequestStatus.tsx) - Table view of all 311 requests with status badges

### Type System

Core types are defined in [frontend/types.ts](frontend/types.ts):

- `RequestStatus` enum: PENDING, PROCESSING, SUBMITTED, FAILED
- `GeminiAnalysis` interface: Represents AI analysis output (requestType, location, details, confidence)
- `Message` interface: WhatsApp message with embedded analysis and automation log
- `Request` interface: 311 request linked to a message via `messageId`

### Styling

- Uses Tailwind CSS via CDN ([frontend/index.html](frontend/index.html))
- Dark theme (gray-900 background)
- Color coding:
  - Blue for messages/WhatsApp data
  - Purple for Gemini analysis
  - Green for automation logs
  - Status-specific colors in request table (green=submitted, yellow=processing, red=failed, gray=pending)

### Path Aliases

TypeScript and Vite are configured with `@/*` alias pointing to frontend directory ([frontend/tsconfig.json](frontend/tsconfig.json), [frontend/vite.config.ts](frontend/vite.config.ts)).

## Backend Architecture

The backend is a **Python/FastAPI** server that handles Twilio webhooks and processes 311 requests.

### Server Structure

**Main Server** ([server/main.py](server/main.py))
- FastAPI app running on port 3001
- Handles CORS for frontend communication
- Supports automatic API documentation at `/docs`

**Routes** ([server/routes/twilio_webhook.py](server/routes/twilio_webhook.py))
- `POST /twilio/webhook` - Main webhook endpoint for incoming WhatsApp messages
- `POST /twilio/status` - Status callback endpoint for message delivery tracking
- Flow:
  1. Receives message from Twilio
  2. Analyzes with Gemini AI
  3. Validates confidence threshold (>0.7)
  4. Submits to SF 311 (simulated)
  5. Sends response back via Twilio

**Services:**
- [gemini.py](server/services/gemini.py) - Gemini AI integration for message analysis
  - Uses `gemini-2.5-flash` model
  - Extracts: requestType, location, details, confidence
  - Returns structured JSON analysis

- [sf311.py](server/services/sf311.py) - SF 311 submission logic
  - **Currently simulated** for demo purposes
  - Generates mock case IDs and automation logs
  - Production version would use browser automation (Playwright) or SF 311 API
  - See inline comments for production implementation reference

**Additional Python Modules:**
- [config.py](server/config.py) - Configuration and environment variable loading
- [storage.py](server/storage.py) - In-memory storage for messages and requests
- [requirements.txt](server/requirements.txt) - Python dependencies

**Python Dependencies Installation:**
```bash
pip install -r server/requirements.txt
```

### Twilio Configuration

For the Twilio WhatsApp Sandbox, configure these webhook URLs:

**When a message comes in:**
```
https://your-domain.com/twilio/webhook
Method: POST
```

**Status callback URL (optional):**
```
https://your-domain.com/twilio/status
Method: POST
```

For local development, use [ngrok](https://ngrok.com/) to expose your local server:
```bash
ngrok http 3001
# Use the HTTPS URL provided (e.g., https://abc123.ngrok.io/twilio/webhook)
```

### Environment Variables

The backend requires these environment variables in `.env.local`:
- `GEMINI_API_KEY` - Your Gemini API key (required)
- `PORT` - Server port (optional, defaults to 3001)
- `TWILIO_ACCOUNT_SID` - Twilio account SID (optional, for validation)
- `TWILIO_AUTH_TOKEN` - Twilio auth token (optional, for validation)

## Key Implementation Notes

- The **frontend dashboard** (in `frontend/`) is a simulation using mock data from [frontend/constants.ts](frontend/constants.ts)
- The **backend** (in `server/`) is implemented in **Python/FastAPI**
- The backend processes real Twilio webhooks with Gemini AI
- SF 311 submission is currently simulated - production would need browser automation or API integration
- Some messages intentionally show different scenarios (successful submission, API errors with retry, demo mode skip)
- React 19.2.0 is used with React.StrictMode enabled
- Frontend and server are completely separated and can be developed/deployed independently
