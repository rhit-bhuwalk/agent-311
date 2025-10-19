import fs from 'fs';

// Test Case 10: Park bench graffiti
console.log('📋 Test Case: Graffiti carved into park bench');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Wooden park bench in Dolores Park near the playground has graffiti carved into it with a knife. Multiple initials and dates carved into the backrest and seat. Located on the north side of the park.',
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
