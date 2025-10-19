import { mapFieldsToData } from './gemini-service.js';
import { handleLocationField } from './location-handler.js';

/**
 * Intelligently detect all fillable fields on the current page
 */
export async function detectPageFields(page) {
  console.log('🔍 Detecting form fields on page...');

  const fields = await page.evaluate(() => {
    const results = [];

    // Helper function to check if element is visible
    function isVisible(element) {
      if (!element) return false;
      const style = window.getComputedStyle(element);
      return style.display !== 'none' &&
             style.visibility !== 'hidden' &&
             style.opacity !== '0' &&
             element.offsetParent !== null;
    }

    // Find all radio button groups
    const radios = document.querySelectorAll('input[type="radio"]');
    const radioGroups = {};
    radios.forEach((radio) => {
      if (!isVisible(radio)) return; // Skip hidden radios
      const name = radio.name || radio.id;
      if (!radioGroups[name]) {
        // Find label for this radio group
        const label = document.querySelector(`label[for="${radio.id}"]`)?.textContent ||
                     radio.closest('label')?.textContent ||
                     radio.parentElement?.textContent ||
                     '';

        // Find question text (usually above the radios)
        const questionElement = radio.closest('fieldset, div')?.querySelector('h1, h2, h3, h4, h5, h6, legend, label, [class*="question"]');
        const question = questionElement?.textContent || '';

        radioGroups[name] = {
          type: 'radio',
          name,
          question: question.trim(),
          label: label.trim(),
          options: [],
          required: radio.required
        };
      }

      const optionLabel = document.querySelector(`label[for="${radio.id}"]`)?.textContent ||
                         radio.closest('label')?.textContent ||
                         radio.value;

      radioGroups[name].options.push({
        value: radio.value,
        label: optionLabel.trim(),
        id: radio.id
      });
    });

    results.push(...Object.values(radioGroups));

    // Find text inputs and textareas
    const textFields = document.querySelectorAll('input[type="text"], input[type="email"], textarea, input:not([type])');
    textFields.forEach((field) => {
      if (!isVisible(field)) return; // Skip hidden fields
      if (field.readOnly || field.disabled) return; // Skip readonly/disabled fields

      const label = document.querySelector(`label[for="${field.id}"]`)?.textContent ||
                   field.placeholder ||
                   field.getAttribute('aria-label') ||
                   field.name ||
                   '';

      results.push({
        type: field.tagName === 'TEXTAREA' ? 'textarea' : 'text',
        id: field.id,
        name: field.name,
        label: label.trim(),
        placeholder: field.placeholder || '',
        required: field.required,
        value: field.value
      });
    });

    // Find select dropdowns
    const selects = document.querySelectorAll('select');
    selects.forEach((select) => {
      if (!isVisible(select)) return; // Skip hidden selects
      const label = document.querySelector(`label[for="${select.id}"]`)?.textContent ||
                   select.name ||
                   '';

      const options = Array.from(select.options).map(opt => ({
        value: opt.value,
        label: opt.textContent.trim()
      }));

      results.push({
        type: 'select',
        id: select.id,
        name: select.name,
        label: label.trim(),
        options,
        required: select.required
      });
    });

    // Detect map/location fields
    const mapContainer = document.querySelector('[class*="map"], [id*="map"], .leaflet-container, .mapboxgl-map');
    if (mapContainer) {
      results.push({
        type: 'map',
        id: 'location-map',
        label: 'Location Map',
        required: true
      });
    }

    // Detect file upload fields
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach((fileInput) => {
      if (!isVisible(fileInput)) return;

      const label = document.querySelector(`label[for="${fileInput.id}"]`)?.textContent ||
                   fileInput.getAttribute('aria-label') ||
                   fileInput.name ||
                   '';

      results.push({
        type: 'file',
        id: fileInput.id,
        name: fileInput.name,
        label: label.trim(),
        required: fileInput.required,
        accept: fileInput.accept || ''
      });
    });

    return results;
  });

  console.log(`✅ Found ${fields.length} fields:`, fields.map(f => {
    if (f.type === 'select' && f.options) {
      return `${f.type}: ${f.label} [${f.options.map(opt => opt.value || opt.label).join(', ')}]`;
    }
    return `${f.type}: ${f.label || f.question}`;
  }));
  return fields;
}

/**
 * Fill the current page based on AI-generated field mapping
 */
export async function fillCurrentPage(page, data) {
  console.log('📝 Filling current page...');

  // Detect what fields are on this page
  const fields = await detectPageFields(page);

  if (fields.length === 0) {
    console.log('⚠️  No fields found on this page');
    return { fieldsFound: 0, fieldsFilled: 0 };
  }

  // Ask Gemini how to map our data to these fields
  const actions = await mapFieldsToData(fields, data);

  let fieldsFilled = 0;
  const processedFields = new Set(); // Track processed fields to avoid duplicates

  // Separate actions into radio buttons and others - do radios first!
  const radioActions = actions.filter(a => a.action === 'select' || a.action === 'click');
  const otherActions = actions.filter(a => a.action !== 'select' && a.action !== 'click');
  const allActions = [...radioActions, ...otherActions];

  // Execute each action
  for (const action of allActions) {
    try {
      if (action.action === 'skip') {
        console.log(`⏭️  Skipping: ${action.field_id} (${action.reasoning})`);
        continue;
      }

      if (action.action === 'needs_special_handling') {
        // Skip if we've already processed a location field on this page
        if (processedFields.has('location-map')) {
          console.log(`⏭️  Skipping duplicate location field: ${action.field_id}`);
          continue;
        }
        console.log(`🗺️  Special handling: ${action.field_id}`);
        await handleLocationField(page, data);
        processedFields.add('location-map');
        fieldsFilled++;
        continue;
      }

      const field = fields.find(f =>
        f.id === action.field_id ||
        f.name === action.field_id ||
        f.label?.includes(action.field_id) ||
        f.question?.includes(action.field_id)
      );

      if (!field) {
        console.log(`⚠️  Field not found: ${action.field_id}, trying direct match...`);
        // Try to select radio button directly by value
        if (action.action === 'select' || action.action === 'click') {
          try {
            const radioField = fields.find(f => f.type === 'radio');
            if (radioField) {
              console.log(`☑️  Trying to select radio option: "${action.value}"`);
              await selectOption(page, radioField, action.value);
              fieldsFilled++;
            }
          } catch (e) {
            console.log(`   ⚠️  Could not select: ${e.message}`);
          }
        }
        continue;
      }

      if (action.action === 'upload') {
        if (data.imagePath) {
          console.log(`📤  Uploading image to "${field.label || field.question}"`);
          await uploadFile(page, field, data.imagePath);
          fieldsFilled++;
        } else {
          console.log(`⏭️  Skipping file upload "${field.label || field.question}" - no image provided`);
        }
      } else if (action.action === 'fill') {
        // Skip if value is null or undefined
        if (action.value === null || action.value === undefined || action.value === 'null') {
          console.log(`⏭️  Skipping "${field.label || field.question}" - no value to fill`);
          continue;
        }
        console.log(`✍️  Filling "${field.label || field.question}" with: "${action.value}"`);
        await fillTextField(page, field, String(action.value));
        fieldsFilled++;
      } else if (action.action === 'select' || action.action === 'click') {
        console.log(`☑️  Selecting "${field.label || field.question}": "${action.value}"`);
        await selectOption(page, field, action.value);
        fieldsFilled++;
      }

      // Small delay for smooth visual effect
      await page.waitForTimeout(150);

    } catch (error) {
      console.error(`❌ Error with field ${action.field_id}:`, error.message);
    }
  }

  // FAILSAFE 1: Always fill description/request fields if they exist and haven't been filled
  const descriptionField = fields.find(f =>
    (f.type === 'textarea' || f.type === 'text') &&
    (f.label?.toLowerCase().includes('description') ||
     f.label?.toLowerCase().includes('request') ||
     f.placeholder?.toLowerCase().includes('description'))
  );

  if (descriptionField && data.description) {
    // Check if we already filled this field
    const alreadyFilled = allActions.some(a =>
      a.field_id === descriptionField.id ||
      a.field_id === descriptionField.name
    );

    if (!alreadyFilled) {
      console.log(`🔧 FAILSAFE: Force-filling description field "${descriptionField.label}" with: "${data.description}"`);
      try {
        await fillTextField(page, descriptionField, data.description);
        fieldsFilled++;
      } catch (error) {
        console.error(`❌ Failsafe fill error: ${error.message}`);
      }
    }
  }


  console.log(`✅ Filled ${fieldsFilled}/${fields.length} fields`);
  return { fieldsFound: fields.length, fieldsFilled };
}

/**
 * Fill a text field
 */
async function fillTextField(page, field, value) {
  const selector = field.id ? `#${field.id}` : `[name="${field.name}"]`;
  await page.fill(selector, value);
}

/**
 * Select an option (radio, checkbox, or dropdown)
 */
async function selectOption(page, field, value) {
  if (field.type === 'radio') {
    // Find the radio button option that matches the value
    const option = field.options.find(opt =>
      opt.label.toLowerCase().includes(value.toLowerCase()) ||
      opt.value.toLowerCase().includes(value.toLowerCase())
    );

    if (option && option.id) {
      console.log(`   → Clicking radio: ${option.label}`);
      await page.click(`#${option.id}`);
    } else {
      // Try clicking by label text directly
      console.log(`   → Trying to find radio by label text containing: ${value}`);
      const radioLabel = await page.locator(`label:has-text("${value}")`).first();
      if (await radioLabel.isVisible({ timeout: 1000 })) {
        await radioLabel.click();
      }
    }
  } else if (field.type === 'select') {
    const selector = field.id ? `#${field.id}` : `[name="${field.name}"]`;

    // Verify the value exists in options
    const validOption = field.options.find(opt => opt.value === value);
    if (!validOption) {
      console.log(`   ⚠️  Value "${value}" not found in dropdown options, trying first match...`);
      // Try to find a close match
      const closeMatch = field.options.find(opt =>
        opt.value.toLowerCase().includes(value.toLowerCase()) ||
        opt.label.toLowerCase().includes(value.toLowerCase())
      );
      if (closeMatch) {
        console.log(`   → Using close match: "${closeMatch.value}" (${closeMatch.label})`);
        value = closeMatch.value;
      } else {
        throw new Error(`Value "${value}" not found in dropdown and no close match available`);
      }
    }

    // Select the option
    await page.selectOption(selector, value);

    // Wait for UI to update
    await page.waitForTimeout(300);

    // Trigger change event to ensure form validation updates
    await page.evaluate((sel) => {
      const element = document.querySelector(sel);
      if (element) {
        element.dispatchEvent(new Event('change', { bubbles: true }));
        element.dispatchEvent(new Event('blur', { bubbles: true }));
      }
    }, selector);

    // Verify the selection stuck
    const selectedValue = await page.evaluate((sel) => {
      const element = document.querySelector(sel);
      return element ? element.value : null;
    }, selector);

    if (selectedValue !== value) {
      throw new Error(`Dropdown selection failed: expected "${value}" but got "${selectedValue}"`);
    }

    console.log(`   ✓ Dropdown value confirmed: "${value}"`);
  }
}

/**
 * Upload a file to a file input field
 */
async function uploadFile(page, field, filePath) {
  const selector = field.id ? `#${field.id}` : `[name="${field.name}"]`;
  await page.setInputFiles(selector, filePath);
}

/**
 * Click the Next button intelligently using fast browser-context detection
 */
export async function clickNext(page) {
  console.log('⏭️  Looking for Next button...');

  try {
    // Wait a moment for any dynamic content to load
    await page.waitForTimeout(500);

    // Find the truly visible and clickable Next button using browser evaluation
    const nextButtonInfo = await page.evaluate(() => {
      const buttons = Array.from(document.querySelectorAll('button, input[type="submit"], input[type="button"]'));

      for (const btn of buttons) {
        const text = (btn.textContent?.trim() || btn.value || '').toLowerCase();

        // Must say "next"
        if (text === 'next') {
          const style = window.getComputedStyle(btn);
          const rect = btn.getBoundingClientRect();

          // Must be truly visible (not just display !== 'none')
          const isVisible = style.display !== 'none' &&
                           style.visibility !== 'hidden' &&
                           style.opacity !== '0' &&
                           rect.width > 0 &&
                           rect.height > 0;

          if (isVisible && !btn.disabled) {
            return {
              id: btn.id,
              text: btn.textContent?.trim() || btn.value
            };
          }
        }
      }
      return null;
    });

    if (nextButtonInfo) {
      console.log(`   ✓ Found Next button (ID: ${nextButtonInfo.id})`);

      // Click by ID to ensure we get the right button
      await page.click(`#${nextButtonInfo.id}`);

      // Wait for navigation or page update
      await page.waitForTimeout(800);

      console.log('✅ Clicked Next');
      return true;
    }

    console.log('⚠️  No visible Next button found');
    return false;

  } catch (error) {
    console.log(`⚠️  Error with Next button: ${error.message}`);
    return false;
  }
}

/**
 * Check if we should select "Report Anonymously" button
 * This requires first selecting "No" on the contact information question
 */
export async function handleAnonymousOption(page) {
  console.log('🔍 Checking for anonymous reporting option...');

  try {
    // Step 1: Check if there's a "Would You Like to Provide Contact Information?" question
    // Click the LABEL for "No" (radio inputs are often hidden by CSS)
    const labelSelectors = [
      'label[for="dform_widget_rad_anonymous_yn2"]',
      'label[for="dform_widget_rad_contact_info2"]',
      'label:has-text("No, I want to remain anonymous")'
    ];

    for (const selector of labelSelectors) {
      try {
        const label = page.locator(selector).first();
        if (await label.isVisible({ timeout: 500 })) {
          console.log(`☑️  Found contact information question - clicking "${await label.textContent()}" label`);
          await label.click();
          console.log('⏳ Waiting for "Report Anonymously" button to appear...');
          await page.waitForTimeout(1500); // Wait for button to appear
          break;
        }
      } catch (e) {
        // Try next selector
      }
    }
  } catch (error) {
    // No contact info question found, might already be on final page
  }

  try {
    // Step 2: Look for "Report Anonymously" button by ID (revealed when "No" is clicked)
    console.log('🔍 Searching for "Report Anonymously" button by ID...');

    const buttonSelectors = [
      '#dform_widget_button_but_V633VQV8',           // Citizen search page button
      '#dform_widget_button_but_anonymous_next',      // Radio Y/N button
      'button:has-text("Report Anonymously")'         // Fallback text search
    ];

    for (const selector of buttonSelectors) {
      try {
        const button = page.locator(selector).first();
        if (await button.isVisible({ timeout: 1000 })) {
          console.log(`☑️  Found "Report Anonymously" button (${selector}) - clicking it`);
          await button.click();
          await page.waitForTimeout(2000);
          console.log('✅ Successfully clicked "Report Anonymously"');
          return true;
        }
      } catch (e) {
        // Try next selector
      }
    }

    console.log('⚠️  "Report Anonymously" button not visible with any selector');
  } catch (error) {
    console.log(`⚠️  Error finding "Report Anonymously" button: ${error.message}`);
  }

  return false;
}
