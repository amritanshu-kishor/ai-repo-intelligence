from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import API_DESCRIPTION, API_TITLE, API_VERSION
from logger import get_logger
from chroma_routes import router as chroma_router
from parser_routes import router as parser_router
from repository_routes import router as repository_router
from cytoscape_routes import router as cytoscape_router
from upload_routes import router as upload_router

logger = get_logger()

app = FastAPI(
    title=API_TITLE,
    version=API_VERSION,
    description=API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(repository_router, prefix="/api/v1")
app.include_router(parser_router, prefix="/api/v1")
app.include_router(chroma_router, prefix="/api/v1")
app.include_router(cytoscape_router)
app.include_router(upload_router, prefix="/api/v1")


@app.on_event("startup")
async def startup_event() -> None:
    logger.info("Repository Intelligence backend starting.")


@app.on_event("shutdown")
async def shutdown_event() -> None:
    logger.info("Repository Intelligence backend shutting down.")
