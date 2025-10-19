"""Configuration module for loading environment variables."""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the parent directory (project root)
project_root = Path(__file__).parent.parent

# Load .env.local from project root
dotenv_path = project_root / '.env.local'
load_dotenv(dotenv_path=dotenv_path)

# Verify API key is loaded
if not os.getenv('GEMINI_API_KEY'):
    print('❌ ERROR: GEMINI_API_KEY not found in environment variables!')
    print('   Please make sure .env.local exists in the project root with GEMINI_API_KEY set.')
    sys.exit(1)


class Config:
    """Application configuration."""
    GEMINI_API_KEY: str = os.getenv('GEMINI_API_KEY', '')
    DEDALUS_API_KEY: str = os.getenv('DEDALUS_API_KEY', '')
    PORT: int = int(os.getenv('PORT', 3001))
    # Twilio credentials (for media download and webhook validation)
    TWILIO_ACCOUNT_SID: str = os.getenv('TWILIO_ACCOUNT_SID', '')
    TWILIO_AUTH_TOKEN: str = os.getenv('TWILIO_AUTH_TOKEN', '')
    TWILIO_API_KEY: str = os.getenv('TWILIO_API_KEY', '')


config = Config()
print('✅ Configuration loaded successfully')
