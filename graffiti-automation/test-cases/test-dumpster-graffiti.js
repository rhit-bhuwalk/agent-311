import fs from 'fs';
import path from 'path';

// Test Case 11: Dumpster graffiti with offensive content
console.log('📋 Test Case: Offensive graffiti on dumpster');

const imagePath = '/Users/edwardzhong/Projects/geminihack2/flow/test-image.png';
const imageBuffer = fs.readFileSync(imagePath);
const imageBase64 = imageBuffer.toString('base64');
console.log(`Image size: ${(imageBuffer.length / 1024).toFixed(2)} KB`);

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Commercial dumpster in the alley behind 1234 Mission Street between 8th and 9th has extremely vulgar and sexually explicit graffiti spray painted in large letters. The content is highly offensive and visible from the street. Urgent removal needed.',
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
