import fs from 'fs';
import path from 'path';

// Test Case 9: USPS mailbox graffiti with image
console.log('📋 Test Case: Graffiti on USPS mailbox');

const imagePath = '/Users/edwardzhong/Projects/geminihack2/flow/test-image.png';
const imageBuffer = fs.readFileSync(imagePath);
const imageBase64 = imageBuffer.toString('base64');
console.log(`Image size: ${(imageBuffer.length / 1024).toFixed(2)} KB`);

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'The blue USPS mailbox on the corner of Market Street and 4th Street has been vandalized with black marker graffiti. Someone drew stick figures and wrote random words all over it. Not offensive content, just unsightly vandalism on federal property.',
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
