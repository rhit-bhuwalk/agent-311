/**
 * Smart location handler with dual strategy:
 * 1. Try to find and use search box (most reliable, looks natural)
 * 2. Fallback to direct coordinate injection if available
 */

export async function handleLocationField(page, data) {
  console.log('🗺️  Handling location field...');

  const location = data.location || data.coordinates;

  if (!location) {
    console.log('⚠️  No location data provided');
    return false;
  }

  // Strategy 1: Search box approach (preferred - looks natural)
  const searchSuccess = await trySearchBoxApproach(page, data.location);
  if (searchSuccess) {
    return true;
  }

  // Strategy 2: Direct coordinate injection
  if (data.coordinates) {
    const coordSuccess = await tryCoordinateInjection(page, data.coordinates);
    if (coordSuccess) {
      return true;
    }
  }

  // Strategy 3: Type in location description field if map fails
  const descSuccess = await tryLocationDescription(page, data.location, data.locationDescription);
  if (descSuccess) {
    return true;
  }

  console.log('❌ All location strategies failed');
  return false;
}

/**
 * Strategy 1: Use the search box with keyboard navigation (most reliable)
 */
async function trySearchBoxApproach(page, locationText) {
  console.log('📍 Trying search box with keyboard navigation...');

  try {
    // Find search input (various possible selectors)
    const searchSelectors = [
      'input[placeholder*="search" i]',
      'input[placeholder*="address" i]',
      'input[placeholder*="location" i]',
      'input[aria-label*="search" i]',
      '[id*="arcgis_search"]',
      '.leaflet-control-geocoder input',
      '[class*="search"] input',
    ];

    let searchBox = null;
    for (const selector of searchSelectors) {
      try {
        searchBox = page.locator(selector).first();
        if (await searchBox.isVisible({ timeout: 1000 })) {
          console.log(`   Found search box: ${selector}`);
          break;
        }
      } catch (e) {
        continue;
      }
    }

    if (!searchBox || !(await searchBox.isVisible({ timeout: 1000 }))) {
      console.log('⚠️  Search box not found');
      return false;
    }

    // Clear any existing value first
    await searchBox.click();
    await searchBox.clear();
    await page.waitForTimeout(50);

    // Type the location faster
    console.log(`⌨️  Typing: "${locationText}"`);
    await searchBox.type(locationText, { delay: 20 });

    // Wait for autocomplete suggestions to appear
    console.log('⏳ Waiting for autocomplete suggestions...');
    await page.waitForTimeout(1500);

    // Strategy A: Use keyboard to navigate and select
    console.log('⬇️  Pressing ArrowDown to select first result');
    await searchBox.press('ArrowDown');
    await page.waitForTimeout(300);

    console.log('⏎ Pressing Enter to confirm selection');
    await searchBox.press('Enter');

    // Wait for map to update with the selected location
    console.log('⏳ Waiting for map to update...');
    await page.waitForTimeout(2000);

    // CRITICAL: Click the map to place the pin and populate VerintObjectReferenceID
    console.log('🗺️  Clicking map to confirm location pin...');
    const mapClicked = await clickMapCenter(page);

    if (mapClicked) {
      console.log('✅ Location confirmed on map');
    } else {
      console.log('⚠️  Could not click map - trying to proceed anyway');
    }

    // Give it a moment to register the click
    await page.waitForTimeout(1000);

    console.log('✅ Search box with keyboard approach successful');
    return true;

  } catch (error) {
    console.log('⚠️  Search box approach failed:', error.message);
    return false;
  }
}

/**
 * Strategy 2: Direct coordinate injection into hidden fields
 */
async function tryCoordinateInjection(page, coordinates) {
  console.log('🎯 Trying coordinate injection...');

  try {
    const { lat, lng } = coordinates;

    // Try to find and set hidden lat/lng fields
    const injected = await page.evaluate(({ lat, lng }) => {
      // Look for various possible input names/ids
      const latFields = [
        document.querySelector('input[name*="lat" i]'),
        document.querySelector('input[id*="lat" i]'),
        document.querySelector('[name="latitude"]'),
      ].filter(Boolean);

      const lngFields = [
        document.querySelector('input[name*="lng" i]'),
        document.querySelector('input[name*="lon" i]'),
        document.querySelector('input[id*="lng" i]'),
        document.querySelector('input[id*="lon" i]'),
        document.querySelector('[name="longitude"]'),
      ].filter(Boolean);

      if (latFields.length > 0 && lngFields.length > 0) {
        latFields[0].value = lat;
        lngFields[0].value = lng;

        // Trigger change events
        latFields[0].dispatchEvent(new Event('change', { bubbles: true }));
        lngFields[0].dispatchEvent(new Event('change', { bubbles: true }));

        return true;
      }

      return false;
    }, { lat, lng });

    if (injected) {
      console.log(`✅ Injected coordinates: ${lat}, ${lng}`);
      await page.waitForTimeout(500);
      await clickMapCenter(page);
      return true;
    } else {
      console.log('⚠️  Could not find lat/lng fields');
      return false;
    }

  } catch (error) {
    console.log('⚠️  Coordinate injection failed:', error.message);
    return false;
  }
}

/**
 * Strategy 3: Fill location description field as fallback
 */
async function tryLocationDescription(page, location, description) {
  console.log('📝 Trying location description field...');

  try {
    // Look for location-related text areas or inputs
    const descSelectors = [
      'textarea[name*="location" i]',
      'textarea[id*="location" i]',
      'input[placeholder*="location" i]',
      'textarea[placeholder*="describe" i]',
    ];

    for (const selector of descSelectors) {
      try {
        const field = page.locator(selector).first();
        if (await field.isVisible({ timeout: 1000 })) {
          const text = description ? `${location}. ${description}` : location;
          console.log(`✍️  Filling location description: "${text}"`);
          await field.fill(text);
          return true;
        }
      } catch (e) {
        continue;
      }
    }

    console.log('⚠️  No location description field found');
    return false;

  } catch (error) {
    console.log('⚠️  Location description failed:', error.message);
    return false;
  }
}

/**
 * Click the center of the map to confirm location selection
 */
async function clickMapCenter(page) {
  console.log('🗺️  Clicking map center...');

  try {
    // Wait for map to render after address selection
    await page.waitForTimeout(1200);

    console.log('   🔍 Searching for map element...');

    // Use page.evaluate() to find map in browser context - MUCH faster!
    const mapInfo = await page.evaluate(() => {
      // Find all visible divs efficiently using browser DOM APIs
      const allDivs = Array.from(document.querySelectorAll('div'));

      let largestMapDiv = null;
      let largestArea = 0;

      for (const div of allDivs) {
        // Skip if not visible
        const style = window.getComputedStyle(div);
        if (style.display === 'none' || style.visibility === 'hidden') continue;

        const rect = div.getBoundingClientRect();
        const area = rect.width * rect.height;

        // Must be at least 400x400 and roughly square (aspect ratio < 3)
        if (rect.width > 400 && rect.height > 400) {
          const aspectRatio = Math.max(rect.width, rect.height) / Math.min(rect.width, rect.height);

          if (aspectRatio < 3 && area > largestArea) {
            const className = div.className || '';
            const id = div.id || '';

            // Prefer map-like elements
            const isMapLike = className.includes('map') || className.includes('esri') ||
                            className.includes('leaflet') || id.includes('map');

            if (isMapLike || area > largestArea * 1.5) {
              largestMapDiv = {
                x: rect.x,
                y: rect.y,
                width: rect.width,
                height: rect.height,
                className: className,
                id: id
              };
              largestArea = area;
            }
          }
        }
      }

      return largestMapDiv;
    });

    if (mapInfo) {
      const centerX = mapInfo.x + mapInfo.width / 2;
      const centerY = mapInfo.y + mapInfo.height / 2;

      console.log(`   ✓ Found map container`);
      console.log(`   → Map size: ${Math.round(mapInfo.width)}x${Math.round(mapInfo.height)}`);
      console.log(`   → Clicking at (${Math.round(centerX)}, ${Math.round(centerY)})`);

      await page.mouse.click(centerX, centerY);
      console.log('   ✅ Clicked map center');
      await page.waitForTimeout(300);
      return true;
    }

    // Fallback: try specific selectors
    console.log('   → Trying specific map selectors...');
    const specificSelectors = [
      '.esri-view-surface',
      '.esri-view',
      '.leaflet-container',
      '.mapboxgl-map'
    ];

    for (const selector of specificSelectors) {
      try {
        const element = page.locator(selector).first();
        if (await element.isVisible({ timeout: 300 })) {
          const box = await element.boundingBox();
          if (box && box.width > 300 && box.height > 300) {
            const centerX = box.x + box.width / 2;
            const centerY = box.y + box.height / 2;

            console.log(`   ✓ Found map: ${selector}`);
            console.log(`   → Clicking at (${Math.round(centerX)}, ${Math.round(centerY)})`);

            await page.mouse.click(centerX, centerY);
            console.log('   ✅ Clicked map center');
            await page.waitForTimeout(400);
            return true;
          }
        }
      } catch (e) {
        continue;
      }
    }

    console.log('⚠️  Could not find suitable map to click');
    return false;

  } catch (error) {
    console.log('⚠️  Map click failed:', error.message);
    return false;
  }
}
