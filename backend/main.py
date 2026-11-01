from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import os
import logging
from dotenv import load_dotenv

from src.config.database import init_db
from src.api.routes import auth, contracts, upload, chat

# Load environment variables
load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

# Note: Backend services are organized as follows:
# - src/services/extraction.py - Contract data extraction
# - src/services/risks.py - Risk identification and analysis
# - src/services/summary.py - Contract summarization
# - src/services/chat.py - Chat functionality
# - src/services/rag.py - RAG implementation for chat & summary

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("🚀 Starting AI CLM Backend...")
    
    # Create uploads directory if it doesn't exist
    upload_dir = os.getenv("UPLOAD_DIR", "./uploads")
    os.makedirs(upload_dir, exist_ok=True)
    
    # Initialize database
    await init_db()
    print("✅ Database initialized")
    
    yield
    
    # Shutdown
    print("👋 Shutting down...")

# Create FastAPI app
app = FastAPI(
    title="AI Contract Lifecycle Management API",
    description="Backend API for AI-powered contract analysis and management",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(contracts.router, prefix="/api/contracts", tags=["Contracts"])
app.include_router(upload.router, prefix="/api/contracts", tags=["Upload"])
app.include_router(chat.router, prefix="/api/chat", tags=["Chat"])

@app.get("/")
async def root():
    return {
        "message": "AI Contract Lifecycle Management API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=True
    )
