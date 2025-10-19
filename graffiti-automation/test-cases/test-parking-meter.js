import fs from 'fs';

// Test Case 14: Parking meter sticker graffiti
console.log('📋 Test Case: Sticker graffiti on parking meters');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Multiple parking meters along Polk Street between Bush and Sutter have been vandalized with stickers. Approximately 10 meters have large stickers covering the payment screens and instructions. Some stickers have political messages, others are just random designs.',
  // No image
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
