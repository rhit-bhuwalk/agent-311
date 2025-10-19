import fs from 'fs';
import path from 'path';

// Test Case 6: Signal box graffiti with image
console.log('📋 Test Case: Signal box graffiti with offensive content');

// Use same test image
const imagePath = '/Users/edwardzhong/Projects/geminihack2/flow/test-image.png';
const imageBuffer = fs.readFileSync(imagePath);
const imageBase64 = imageBuffer.toString('base64');
console.log(`Image size: ${(imageBuffer.length / 1024).toFixed(2)} KB`);

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Traffic signal control box on the northeast corner of Van Ness Avenue and Market Street in San Francisco has been vandalized with extremely offensive racial slurs and hate symbols spray painted in black and white. The graffiti covers most of the signal box surface and is highly visible to pedestrians and drivers. This needs urgent removal due to the hateful and discriminatory nature of the content.',
  image: `data:image/png;base64,${imageBase64}`
};

fetch('http://localhost:3000/api/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(payload)
})
  .then(res => res.json())
  .then(data => console.log('✅ Response:', data))
  .catch(err => console.error('❌ Error:', err));
