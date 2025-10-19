import fs from 'fs';

// Test Case 8: Fence graffiti with gang tags
console.log('📋 Test Case: Gang-related graffiti on fence');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Chain-link fence along the basketball court at Mission Playground (19th and Valencia) has been spray painted with gang-related tags and symbols. Multiple colors including red and blue. The graffiti is approximately 15 feet long and covers a significant portion of the fence facing the street. Need removal ASAP as this appears to be territory marking.',
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
