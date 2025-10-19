import fs from 'fs';

// Test Case 12: Bus shelter graffiti
console.log('📋 Test Case: Graffiti on bus shelter');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Muni bus shelter on Geary Boulevard near Masonic Avenue has graffiti etched into the glass panels. Someone used a sharp object to scratch tags and designs into multiple glass panes. The etching makes it difficult to see through the glass clearly.',
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
