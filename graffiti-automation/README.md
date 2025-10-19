# Graffiti Form Automation

Automated SF 311 graffiti reporting form submission using Playwright browser automation and Gemini AI for intelligent form field mapping.

## Features

- Automated multi-page form navigation
- AI-powered form field detection and mapping using Google Gemini
- Intelligent dropdown selection with fuzzy matching
- Support for image uploads
- Address geocoding and auto-completion
- Comprehensive test suite with 14 test cases

## Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Environment Variables

Create a `.env` file:

```env
GEMINI_API_KEY=your_gemini_api_key_here
PORT=3000
```

### 3. Start the Server

```bash
npm start
```

Server will run on `http://localhost:3000`

## API Endpoints

### POST /api/submit

Submit a graffiti report to SF 311.

**Request Body:**
```json
{
  "formUrl": "https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti",
  "description": "There is graffiti at 508 Golden Gate Ave. Spray painted profanity on public property.",
  "image": "data:image/png;base64,..." // Optional base64 encoded image
}
```

**Response:**
```json
{
  "success": true,
  "message": "Form submitted successfully",
  "submissionId": "SR12345678"
}
```

## Test Cases

The `test-cases/` directory contains 14 comprehensive test cases:

1. Offensive graffiti on utility pole
2. Non-offensive street art
3. Bridge graffiti
4. Private property graffiti
5. Sidewalk graffiti (detailed description)
6. Signal box graffiti (offensive)
7. Street sign graffiti
8. Fence graffiti (gang tags)
9. Mailbox graffiti
10. Park bench graffiti
11. Dumpster graffiti (offensive)
12. Bus shelter graffiti
13. Electrical box graffiti (artistic)
14. Parking meter stickers

### Run All Tests

```bash
node test-cases/run-all-tests.js
```

Tests run sequentially with 10-second delays to respect Gemini API rate limits (10 requests/minute).

### Run Individual Test

```bash
node test-cases/test-offensive-graffiti.js
```

## Architecture

### Core Components

1. **server.js** - Express server with /api/submit endpoint
2. **form-filler.js** - Playwright-based form automation with:
   - Multi-page navigation
   - Field detection and classification
   - Enhanced dropdown selection with event triggering
   - Image upload handling
3. **gemini-service.js** - Gemini AI integration for:
   - Form field mapping from description
   - Intelligent value extraction
4. **location-handler.js** - Address geocoding and auto-completion

### Key Fix: Dropdown Selection

The enhanced dropdown selection ensures proper form validation:

```javascript
// Select option
await page.selectOption(selector, value);

// Wait for UI to update
await page.waitForTimeout(300);

// Trigger events for form validation
await page.evaluate((sel) => {
  const element = document.querySelector(sel);
  if (element) {
    element.dispatchEvent(new Event('change', { bubbles: true }));
    element.dispatchEvent(new Event('blur', { bubbles: true }));
  }
}, selector);

// Verify selection persisted
const selectedValue = await page.evaluate(...);
if (selectedValue !== value) {
  throw new Error(`Dropdown selection failed`);
}
```

## Integration with agent-311

This module is designed to be called by the Python backend in `server/services/dedalus_service.py`:

```python
def submit_sf311_form(form_url: str, description: str, image_base64: str = "") -> str:
    api_url = "http://localhost:3000/api/submit"
    payload = {
        "formUrl": form_url,
        "description": description
    }
    if image_base64:
        payload["imageBase64"] = image_base64

    response = requests.post(api_url, json=payload, timeout=30)
    return response.json()
```

## Deployment

For production deployment:

1. Update `dedalus_service.py` to use the production URL instead of localhost
2. Or run as a separate microservice accessible to the Python backend
3. Consider using PM2 or similar for process management
4. Increase timeout values for slower network conditions

## Requirements

- Node.js 18+
- Google Gemini API key (free tier: 10 requests/minute)
- Playwright (automatically installs browser binaries)
