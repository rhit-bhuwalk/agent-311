import fs from 'fs';

// E2E Test: Complete graffiti submission with real image (agent-311 copy)
console.log('🧪 E2E TEST: Graffiti submission with image');
console.log('=' .repeat(60));

const imagePath = '/Users/edwardzhong/Projects/agent-311/graffiti.jpg';

// Check if image exists
if (!fs.existsSync(imagePath)) {
  console.error('❌ Error: graffiti.jpg not found at:', imagePath);
  process.exit(1);
}

const imageBuffer = fs.readFileSync(imagePath);
const imageBase64 = imageBuffer.toString('base64');
console.log(`📸 Image loaded: ${(imageBuffer.length / 1024).toFixed(2)} KB`);

const payload = {
  formUrl: 'https://sanfrancisco.form.us.empro.verintcloudservices.com/form/auto/pw_graffiti',
  description: 'There is graffiti at 1234 Market Street, San Francisco. Large spray painted tags covering the wall near the bus stop. The graffiti contains offensive language and symbols that should be removed urgently.',
  image: `data:image/jpeg;base64,${imageBase64}`
};

console.log('\n📋 Test Details:');
console.log('   Location: 1234 Market Street, San Francisco');
console.log('   Description length:', payload.description.length, 'characters');
console.log('   Image size:', (imageBase64.length / 1024).toFixed(2), 'KB (base64)');
console.log('   Form URL:', payload.formUrl);

console.log('\n🚀 Submitting to graffiti automation service...');
console.log('-'.repeat(60));

const startTime = Date.now();

fetch('http://localhost:3000/api/submit', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify(payload)
})
  .then(res => {
    const duration = ((Date.now() - startTime) / 1000).toFixed(2);
    console.log(`\n⏱️  Response received in ${duration} seconds`);
    console.log('HTTP Status:', res.status, res.statusText);
    return res.json();
  })
  .then(data => {
    console.log('\n📥 Response Data:');
    console.log(JSON.stringify(data, null, 2));

    if (data.success) {
      console.log('\n✅ E2E TEST PASSED!');
      console.log('   Form submitted successfully');
      if (data.submissionId) {
        console.log('   Submission ID:', data.submissionId);
      }
    } else {
      console.log('\n❌ E2E TEST FAILED!');
      console.log('   Error:', data.error || data.message);
      process.exit(1);
    }

    console.log('\n' + '='.repeat(60));
  })
  .catch(err => {
    console.error('\n❌ E2E TEST FAILED!');
    console.error('   Network/Connection Error:', err.message);
    console.error('\n💡 Make sure the graffiti automation service is running:');
    console.error('   cd /Users/edwardzhong/Projects/agent-311/graffiti-automation');
    console.error('   npm start');
    process.exit(1);
  });
