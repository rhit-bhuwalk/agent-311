import fs from 'fs';

// Test Case 7: Street sign graffiti
console.log('📋 Test Case: Graffiti on street sign');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'The stop sign at the intersection of Columbus Avenue and Broadway in San Francisco has been defaced with marker graffiti. Someone wrote tags and drew symbols on both the front and back of the sign, making it less visible and professional-looking. Not offensive language, just vandalism that should be cleaned.',
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
