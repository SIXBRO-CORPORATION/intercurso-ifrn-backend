import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from persistence.database import init_db, engine

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting API")
    init_db()
    logger.info("Database initialized")

    yield

    logger.info("Shutting down API")
    engine.dispose()

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

register_exception_handlers(app)

app.include_router(user_router, prefix="/api", tags=["users"])

app.get("/")
async def root():
    return {
        "status": "ok",
        "message": "API is running",
        "version": "1.0.0"
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "web.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
