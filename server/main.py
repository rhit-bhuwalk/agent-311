"""Main FastAPI application for the WhatsApp 311 bot backend."""
from datetime import datetime
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

try:
    # Try absolute imports (for local development)
    from server.config import config
    from server.routes.twilio_webhook import router as twilio_router
    from server.services.gemini import GEMINI_MODELS
    from server.storage import get_messages, get_requests
except ModuleNotFoundError:
    # Fall back to relative imports (for Railway deployment)
    from config import config
    from routes.twilio_webhook import router as twilio_router
    from services.gemini import GEMINI_MODELS
    from storage import get_messages, get_requests

# Create FastAPI app
app = FastAPI(
    title="WhatsApp 311 Bot API",
    description="Backend API for SF 311 WhatsApp submission bot",
    version="1.0.0"
)

# Store current model selection (in production, use a database)
current_model = GEMINI_MODELS['FLASH']

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your frontend domain
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(twilio_router)


# Pydantic models for API responses
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str


class ModelInfo(BaseModel):
    """Model information."""
    id: str
    name: str


class ModelsResponse(BaseModel):
    """Available models response."""
    available: List[ModelInfo]
    current: str


class ModelSelectRequest(BaseModel):
    """Model selection request."""
    model: str


class ModelSelectResponse(BaseModel):
    """Model selection response."""
    success: bool
    model: str


# Routes
@app.get('/health', response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
    }


@app.get('/api/messages')
async def get_all_messages() -> List[Dict[str, Any]]:
    """Get all messages."""
    return get_messages()


@app.get('/api/requests')
async def get_all_requests() -> List[Dict[str, Any]]:
    """Get all requests."""
    return get_requests()


@app.get('/api/models', response_model=ModelsResponse)
async def get_available_models():
    """Get available Gemini models."""
    available = [
        {'id': value, 'name': key}
        for key, value in GEMINI_MODELS.items()
    ]
    return {
        'available': available,
        'current': current_model
    }


@app.post('/api/models/select', response_model=ModelSelectResponse)
async def select_model(request: ModelSelectRequest):
    """Set current Gemini model."""
    global current_model

    if request.model not in GEMINI_MODELS.values():
        raise HTTPException(
            status_code=400,
            detail={
                'error': 'Invalid model',
                'available': list(GEMINI_MODELS.values())
            }
        )

    current_model = request.model
    print(f'🔄 Model changed to: {request.model}')

    return {
        'success': True,
        'model': current_model
    }


if __name__ == '__main__':
    import uvicorn

    print(f'🚀 Starting server on http://localhost:{config.PORT}')
    print(f'📱 Twilio webhook URL: http://localhost:{config.PORT}/twilio/webhook')

    uvicorn.run(
        app,
        host='0.0.0.0',
        port=config.PORT,
        log_level='info'
    )
