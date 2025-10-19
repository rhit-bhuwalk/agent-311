import express from 'express';
import cors from 'cors';
import { submitForm } from './browser-automation.js';

const app = express();
const PORT = process.env.PORT || 3002;

app.use(cors());
app.use(express.json({ limit: '50mb' })); // Increased limit for base64 images
app.use(express.static('public'));

/**
 * Main API endpoint
 * POST /api/submit
 * Body: { formUrl: string, description: string, image?: string (base64) }
 */
app.post('/api/submit', async (req, res) => {
  const { formUrl, description, image } = req.body;

  if (!formUrl || !description) {
    return res.status(400).json({
      error: 'Missing required fields: formUrl and description'
    });
  }

  console.log('\n' + '='.repeat(60));
  console.log('📨 New submission request received');
  console.log('='.repeat(60));

  try {
    const result = await submitForm(formUrl, description, image);

    if (result.success) {
      res.json({
        success: true,
        message: 'Form submitted successfully!'
      });
    } else {
      res.status(500).json({
        success: false,
        error: result.error || 'Form submission failed'
      });
    }
  } catch (error) {
    console.error('Server error:', error);
    res.status(500).json({
      success: false,
      error: error.message
    });
  }
});

/**
 * Health check
 */
app.get('/health', (req, res) => {
  res.json({ status: 'ok' });
});

app.listen(PORT, () => {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`🤖 Gemini Form Automation Server`);
  console.log(`${'='.repeat(60)}`);
  console.log(`🌐 Server running at: http://localhost:${PORT}`);
  console.log(`📡 API endpoint: POST http://localhost:${PORT}/api/submit`);
  console.log(`🎨 Demo UI: http://localhost:${PORT}`);
  console.log(`${'='.repeat(60)}\n`);
});
