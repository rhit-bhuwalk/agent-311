import fs from 'fs';
import path from 'path';

// Test Case 5: Detailed sidewalk graffiti report
console.log('📋 Test Case: Sidewalk graffiti with detailed description');

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'Multiple layers of spray painted graffiti tags covering approximately 20 feet of sidewalk concrete in front of 456 Haight Street, San Francisco. The tags include various colors - primarily black, blue, and red spray paint. Located on the south side of Haight Street between Fillmore and Steiner. The graffiti appears fresh (less than 24 hours old) and is not offensive in nature, just unsightly tagging.',
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
