import { GoogleGenerativeAI } from '@google/generative-ai';
import dotenv from 'dotenv';

dotenv.config();

const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const model = genAI.getGenerativeModel({ model: 'gemini-2.0-flash-exp' });

/**
 * Parse natural language input into structured form data
 */
export async function parseInput(naturalLanguageInput) {
  console.log('🤖 Gemini: Parsing input...');

  const prompt = `Extract structured data from this graffiti report description. Return ONLY valid JSON with no markdown formatting.

Input: "${naturalLanguageInput}"

Extract:
- issueType: one of ["private_property", "public_property", "illegal_postings"] (default: "public_property")
- location: full address or location description
- coordinates: {lat, lng} if mentioned, else null
- locationDescription: additional details about where exactly the issue is
- requestDescription: description of what needs to be done
- additionalDetails: any other relevant information

Return only the JSON object.`;

  const result = await model.generateContent(prompt);
  const text = result.response.text().trim();

  // Remove markdown code blocks if present
  const jsonText = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const parsed = JSON.parse(jsonText);

  console.log('✅ Extracted:', JSON.stringify(parsed, null, 2));
  return parsed;
}

/**
 * AI-powered field mapping: Figures out which form fields should get which values
 */
export async function mapFieldsToData(fields, data) {
  console.log(`🤖 Gemini: Mapping ${fields.length} form fields to data...`);

  const prompt = `You are a form-filling assistant. Given form fields and user data, map the data to appropriate fields.

FORM FIELDS:
${JSON.stringify(fields, null, 2)}

USER DATA:
${JSON.stringify(data, null, 2)}

RULES:
1. Map data values to the most appropriate field based on labels, names, and types
2. For radio buttons about issue type (graffiti on private/public property), select based on issueType in data
3. For location/map fields or anything with "map" in the label, mark as "needs_special_handling"
4. For file upload fields (type: "file"), use action "upload" if imagePath is present in data, otherwise "skip"
5. For contact info fields (name, phone, email), mark as "skip" (submitting anonymously)
6. For any field asking about reference numbers, IDs, or technical fields, mark as "skip"
7. CRITICAL: For dropdown "What is your request regarding?" - ALWAYS fill it with action "select":
   - If the description mentions offensive content (racial slurs, profanity), select "Offensive"
   - Otherwise, select "Not Offensive" (default)
8. CRITICAL: For dropdown "Request type" - ALWAYS fill it with action "select":
   - Look at the "options" array in the field object to see available choices
   - Select the VALUE (not label) that best matches the description
   - Prefer specific types: pole, street, bridge, sidewalk_structure, etc.
   - IMPORTANT: Avoid selecting building_* options as they may be disabled
   - Default to "other" if unsure or if building-related graffiti
   - ONLY use values that exist in the options array
9. Only fill fields that are clearly relevant to reporting the issue (location, description, issue type)
10. If unsure about a field, mark it as "skip"
11. Return valid JSON only, no markdown

Return JSON array of actions:
[
  {
    "field_id": "field identifier from input",
    "action": "fill" | "select" | "click" | "skip" | "upload" | "needs_special_handling",
    "value": "value to fill/select" or null,
    "reasoning": "why this mapping"
  }
]`;

  const result = await model.generateContent(prompt);
  const text = result.response.text().trim();
  const jsonText = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  const actions = JSON.parse(jsonText);

  console.log(`✅ Generated ${actions.length} actions`);
  return actions;
}

/**
 * Determine if we should proceed to next page
 */
export async function shouldClickNext(pageContent, currentData) {
  const prompt = `You are analyzing a form submission page. Determine if we should click "Next" or if we're done.

PAGE INDICATORS: ${pageContent}
DATA FILLED: ${JSON.stringify(currentData)}

Return JSON: {"clickNext": true/false, "reason": "explanation"}`;

  const result = await model.generateContent(prompt);
  const text = result.response.text().trim();
  const jsonText = text.replace(/```json\n?/g, '').replace(/```\n?/g, '').trim();
  return JSON.parse(jsonText);
}
