"""
Nia Learning Assistant - Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from config import settings
from database import init_db, close_db
from routers import auth, children, conversation

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events - startup and shutdown"""
    logger.info("Starting Nia Learning Assistant...")
    await init_db()
    
    from database import async_session_maker
    from services.content_service import ContentService
    
    async with async_session_maker() as db:
        content_service = ContentService()
        count = await content_service.ingest_all_content(db)
        logger.info(f"Loaded {count} educational content files")
    
    yield
    
    logger.info("Shutting down Nia Learning Assistant...")
    await close_db()


app = FastAPI(
    title="Nia Learning Assistant API",
    description="COPPA-compliant AI learning assistant for K-12 students",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(children.router, prefix="/api/children", tags=["Children"])
app.include_router(conversation.router, prefix="/api/conversation", tags=["Conversation"])


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Nia Learning Assistant API",
        "version": "2.0.0",
        "status": "healthy"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "database": "connected"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.PORT,
        reload=settings.DEBUG
    )
