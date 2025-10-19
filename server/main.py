"""Main FastAPI application for the WhatsApp bot backend."""
from datetime import datetime
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from contextlib import asynccontextmanager

try:
    # Try absolute imports (for local development)
    from server.config import config
    from server.routes.twilio_webhook import router as twilio_router
    from server.database import init_db
except ModuleNotFoundError:
    # Fall back to relative imports (for deployment)
    from config import config
    from routes.twilio_webhook import router as twilio_router
    from database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    print("🚀 Starting up...")
    await init_db()
    yield
    print("👋 Shutting down...")


# Create FastAPI app
app = FastAPI(
    title="WhatsApp Bot API",
    description="Backend API for WhatsApp message storage with Gemini AI",
    version="1.0.0",
    lifespan=lifespan
)

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


# Routes
@app.get('/health', response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return {
        'status': 'ok',
        'timestamp': datetime.now().isoformat()
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
