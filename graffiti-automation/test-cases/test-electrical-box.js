import fs from 'fs';
import path from 'path';

// Test Case 13: Electrical utility box with artistic graffiti
console.log('📋 Test Case: Artistic graffiti on electrical box');

const imagePath = '/Users/edwardzhong/Projects/geminihack2/flow/test-image.png';
const imageBuffer = fs.readFileSync(imagePath);
const imageBase64 = imageBuffer.toString('base64');
console.log(`Image size: ${(imageBuffer.length / 1024).toFixed(2)} KB`);

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'PG&E electrical utility box on the corner of Hyde and California has been painted with colorful street art depicting a cityscape. While artistic, it is unauthorized graffiti on city infrastructure. The art covers all four sides of the box.',
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
