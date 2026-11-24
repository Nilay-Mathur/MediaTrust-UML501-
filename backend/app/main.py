from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging import logger
from app.database.session import engine, Base
from app.api.v1.endpoints import router as api_v1_router

# Initialize database schema
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="Real-Time Digital Trust and Safety Layer: AI-Powered Deepfake, Scam, and Impersonation Analysis Platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits local development, Vite dev server, and Chrome/Edge extensions
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Centralized Error Handling - Security: Hide sensitive stack traces
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception at {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "status": "error",
            "message": "An internal processing error occurred. The technical event has been logged for audit.",
            "path": request.url.path
        }
    )

# Mount API routers
app.include_router(api_v1_router, prefix="/api/v1")

@app.get("/", tags=["Root"])
def root():
    return {
        "service": settings.APP_NAME,
        "version": settings.VERSION,
        "description": "MediaTrust Unified Cybersecurity & Machine Learning Inspection API",
        "docs_url": "/docs",
        "health_url": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
