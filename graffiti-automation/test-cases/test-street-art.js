import fs from 'fs';
import path from 'path';

// Test Case 2: Non-offensive street art/tagging without image
console.log('📋 Test Case: Non-offensive street art on building');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Colorful street art tags on building wall at 1234 Mission Street, San Francisco. Not offensive, just unwanted tagging.',
  // No image provided
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
