# Test Cases for Graffiti Form Automation

This directory contains test cases demonstrating the form automation with various scenarios.

## Prerequisites

- Server must be running: `npm start`
- Server runs on `http://localhost:3000`

## Test Cases

### 1. Offensive Graffiti on Utility Pole (with image)
**File:** `test-offensive-graffiti.js`

**Scenario:**
- Location: Market Street and 5th Street, San Francisco
- Description: Racist slurs on utility pole
- Expected behavior:
  - Selects "Graffiti on Public Property"
  - Marks as "Offensive"
  - Request type: "Pole"
  - Uploads image

**Run:**
```bash
node test-cases/test-offensive-graffiti.js
```

---

### 2. Non-Offensive Street Art (no image)
**File:** `test-street-art.js`

**Scenario:**
- Location: 1234 Mission Street, San Francisco
- Description: Colorful street art tags on building
- Expected behavior:
  - Selects "Graffiti on Public Property"
  - Marks as "Not Offensive" (default)
  - Request type: "Other" (default)
  - No image upload

**Run:**
```bash
node test-cases/test-street-art.js
```

---

### 3. Graffiti on Bridge Structure (with image)
**File:** `test-bridge-graffiti.js`

**Scenario:**
- Location: Bay Bridge overpass near Embarcadero, San Francisco
- Description: Tags on concrete support beams
- Expected behavior:
  - Selects "Graffiti on Public Property"
  - Marks as "Not Offensive"
  - Request type: "Bridge"
  - Uploads image

**Run:**
```bash
node test-cases/test-bridge-graffiti.js
```

---

### 4. Private Property Graffiti (no image)
**File:** `test-private-property.js`

**Scenario:**
- Location: 789 Valencia Street, San Francisco
- Description: Gang tags on private fence
- Expected behavior:
  - Selects "Graffiti on Private Property"
  - Marks as "Not Offensive"
  - Request type: "Other"
  - No image upload

**Run:**
```bash
node test-cases/test-private-property.js
```

---

## Running All Tests

To run all test cases sequentially:

```bash
node test-cases/run-all-tests.js
```

## Expected Results

All tests should complete with:
```json
{ "success": true, "message": "Form submitted successfully!" }
```

## What Gets Tested

- ✅ Location detection and geocoding
- ✅ Public vs Private property classification
- ✅ Offensive vs Non-offensive content detection
- ✅ Request type inference (Pole, Bridge, Street, Other)
- ✅ Image upload (when provided)
- ✅ Anonymous submission
- ✅ Multi-page form navigation
