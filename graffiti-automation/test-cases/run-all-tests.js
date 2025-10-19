// Run all test cases sequentially with delays
const tests = [
  { name: 'Offensive Graffiti on Pole', file: './test-offensive-graffiti.js' },
  { name: 'Non-Offensive Street Art', file: './test-street-art.js' },
  { name: 'Bridge Graffiti', file: './test-bridge-graffiti.js' },
  { name: 'Private Property Graffiti', file: './test-private-property.js' },
  { name: 'Sidewalk Graffiti (Detailed)', file: './test-sidewalk-graffiti.js' },
  { name: 'Signal Box Graffiti (Offensive)', file: './test-signal-box.js' },
  { name: 'Street Sign Graffiti', file: './test-street-sign.js' },
  { name: 'Fence Graffiti (Gang Tags)', file: './test-fence-graffiti.js' },
  { name: 'Mailbox Graffiti', file: './test-mailbox-graffiti.js' },
  { name: 'Park Bench Graffiti', file: './test-bench-graffiti.js' },
  { name: 'Dumpster Graffiti (Offensive)', file: './test-dumpster-graffiti.js' },
  { name: 'Bus Shelter Graffiti', file: './test-bus-shelter.js' },
  { name: 'Electrical Box Graffiti (Artistic)', file: './test-electrical-box.js' },
  { name: 'Parking Meter Stickers', file: './test-parking-meter.js' },
];

async function runAllTests() {
  console.log('🧪 Running all test cases...\n');
  console.log('=' .repeat(60));

  for (let i = 0; i < tests.length; i++) {
    const test = tests[i];
    console.log(`\n📋 Test ${i + 1}/${tests.length}: ${test.name}`);
    console.log('-'.repeat(60));

    try {
      // Dynamically import and run the test
      await import(test.file);

      // Wait 10 seconds before next test to avoid API rate limits (max 10 requests/minute)
      if (i < tests.length - 1) {
        console.log('\n⏳ Waiting 10 seconds before next test to avoid API rate limits...');
        await new Promise(resolve => setTimeout(resolve, 10000));
      }
    } catch (error) {
      console.error(`❌ Test failed: ${error.message}`);
    }
  }

  console.log('\n' + '='.repeat(60));
  console.log('✅ All tests completed!\n');
}

runAllTests();
