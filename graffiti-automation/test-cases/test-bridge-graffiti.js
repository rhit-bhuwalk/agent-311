import fs from 'fs';
import path from 'path';

// Test Case 3: Graffiti on bridge with image
const imagePath = '/Users/edwardzhong/Projects/geminihack2/flow/test-image.png';
const imageBuffer = fs.readFileSync(imagePath);
const base64Image = 'data:image/png;base64,' + imageBuffer.toString('base64');

console.log('📋 Test Case: Graffiti on bridge structure');
console.log('Image size:', Math.round(base64Image.length / 1024), 'KB');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Large graffiti tags on Bay Bridge overpass near Embarcadero, San Francisco. Multiple colors painted on concrete support beams.',
  image: base64Image
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
