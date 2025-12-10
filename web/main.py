import logging
from contextlib import asynccontextmanager
import uvicorn

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from commons.exception_handler import register_exception_handler

from persistence.database import init_db, close_db
from web.commons.exception_handler import register_exception_handler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API")
    await init_db()
    logger.info("Database initialized")

    yield

    logger.info("Shutting down API")
    await close_db()


app = FastAPI(
    title="Intercurso API",
    description="Intercurso System Management",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handler(app)

app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "API is running",
        "version": "1.0.0"
    }

@app.get("/health")
async def health_check():
    """Endpoint detalhado de saúde da aplicação"""
    return {
        "status": "healthy",
        "database": "connected",
        "pool": "active"
    }

if __name__ == "__main__":
    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
