import fs from 'fs';
import path from 'path';

// Test Case 4: Graffiti on private property without image
console.log('📋 Test Case: Graffiti on private property (no image)');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Gang tags on private fence at 789 Valencia Street, San Francisco. Owner wants it removed.',
  // No image - testing without image upload
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
