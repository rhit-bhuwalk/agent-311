import { chromium } from 'playwright';
import { parseInput } from './gemini-service.js';
import { fillCurrentPage, clickNext, handleAnonymousOption } from './form-filler.js';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

/**
 * Main automation orchestrator
 */
export async function submitForm(formUrl, naturalLanguageInput, imageBase64 = null) {
  console.log('\n🚀 Starting form automation...');
  console.log(`📄 Form URL: ${formUrl}`);
  console.log(`💬 Input: "${naturalLanguageInput}"`);
  if (imageBase64) console.log(`📷 Image: Provided (${(imageBase64.length / 1024).toFixed(2)} KB)`);
  console.log();

  let browser;
  let success = false;
  let error = null;
  let imagePath = null;

  try {
    // Step 0: Save image if provided
    if (imageBase64) {
      const tempDir = path.join(__dirname, '../temp');
      if (!fs.existsSync(tempDir)) {
        fs.mkdirSync(tempDir, { recursive: true });
      }

      imagePath = path.join(tempDir, `upload-${Date.now()}.png`);
      const base64Data = imageBase64.replace(/^data:image\/\w+;base64,/, '');
      fs.writeFileSync(imagePath, Buffer.from(base64Data, 'base64'));
      console.log(`💾 Image saved to: ${imagePath}\n`);
    }

    // Step 1: Parse input with Gemini
    const data = await parseInput(naturalLanguageInput);
    data.imagePath = imagePath; // Add image path to data

    // Step 2: Launch visible browser for demo effect
    console.log('🌐 Launching browser...');
    browser = await chromium.launch({
      headless: false, // Visible for demo!
      slowMo: 30, // Minimal slowdown for visibility
    });

    const context = await browser.newContext({
      viewport: { width: 1400, height: 900 },
    });

    const page = await context.newPage();

    // Step 3: Navigate to form
    console.log(`📡 Navigating to ${formUrl}...`);
    await page.goto(formUrl, { waitUntil: 'networkidle' });
    await page.waitForTimeout(500);

    // Step 4: Fill form adaptively, page by page
    let pageCount = 0;
    const maxPages = 10; // Safety limit

    while (pageCount < maxPages) {
      pageCount++;
      console.log(`\n📄 === PAGE ${pageCount} ===`);

      // Check for anonymous option first (this will click "No" if the question appears)
      const anonymousHandled = await handleAnonymousOption(page);

      if (anonymousHandled) {
        // Successfully clicked Report Anonymously button
        console.log('\n✅ Form submitted successfully!');
        success = true;
        break;
      }

      // Fill current page
      const result = await fillCurrentPage(page, data);

      if (result.fieldsFound === 0) {
        console.log('ℹ️  No more fields to fill');
        // No fields found - might be on a page with just the anonymous question
        // Try one more time to handle anonymous option
        const retry = await handleAnonymousOption(page);
        if (retry) {
          console.log('\n✅ Form submitted successfully!');
          success = true;
        }
        break;
      }

      // Try to click Next
      const hasNext = await clickNext(page);

      if (!hasNext) {
        // No Next button found - try Submit
        const submitted = await trySubmit(page);
        if (submitted) {
          console.log('\n✅ Form submitted successfully!');
          success = true;
        }
        break;
      }

      // Small delay between pages
      await page.waitForTimeout(500);
    }

    if (pageCount >= maxPages) {
      throw new Error('Maximum page limit reached');
    }

    // Keep browser open for a moment to show completion
    if (success) {
      console.log('\n🎉 Keeping browser open for 3 seconds to show result...');
      await page.waitForTimeout(3000);
    }

  } catch (err) {
    console.error('\n❌ Error:', err.message);
    error = err.message;
  } finally {
    if (browser) {
      await browser.close();
      console.log('🔒 Browser closed\n');
    }

    // Cleanup temp image file
    if (imagePath && fs.existsSync(imagePath)) {
      fs.unlinkSync(imagePath);
      console.log('🗑️  Cleaned up temp image file\n');
    }
  }

  return { success, error };
}

/**
 * Try to find and click Submit button or Report Anonymously
 */
async function trySubmit(page) {
  console.log('🔍 Looking for Submit or Report Anonymously button...');

  const submitStrategies = [
    () => page.click('button:has-text("Report Anonymously")'),
    () => page.click('button:has-text("Submit")'),
    () => page.click('button[type="submit"]'),
    () => page.click('input[type="submit"]'),
    () => page.click('button:has-text("Send")'),
    () => page.click('button:has-text("Complete")'),
    () => page.click('button:has-text("Finish")'),
    () => page.click('[class*="submit"]'),
  ];

  for (const strategy of submitStrategies) {
    try {
      await strategy();
      console.log('✅ Clicked Submit/Report Anonymously');
      await page.waitForTimeout(2000);
      return true;
    } catch (error) {
      // Try next strategy
    }
  }

  console.log('⚠️  No Submit button found');
  return false;
}
