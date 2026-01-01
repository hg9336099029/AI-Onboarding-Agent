"""
FastAPI Application Entry Point

Main application setup with middleware, CORS, and route registration.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from .api.routes import router, init_routes
from .api.controllers import RepositoryController, QueryController, FileController
from .agent import CodebaseAgent
from .embeddings import CodeEmbedder, VectorStore
from .storage import Database, StorageService
from .ingestion import RepositoryLoader, IngestionService
from .utils import LLMClient
from .config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan"""
    # Startup
    logger.info("Starting AI Codebase Onboarding API")
    
    # Initialize database
    database = Database(settings.DATABASE_URL)
    database.create_tables()
    logger.info("Database initialized")
    
    # Initialize storage service
    storage_service = StorageService(database)
    
    # Initialize embedder (supports free HuggingFace or paid OpenAI)
    embedder = CodeEmbedder(
        provider=settings.EMBEDDING_PROVIDER,
        api_key=settings.OPENAI_API_KEY if settings.EMBEDDING_PROVIDER == "openai" else None,
        model=settings.EMBEDDING_MODEL
    )
    logger.info(f"Embedder initialized with {settings.EMBEDDING_PROVIDER}")
    
    # Initialize vector store
    vector_store = VectorStore(
        dimension=embedder.dimension,  # Auto-detect from embedder
        index_path=settings.VECTOR_STORE_PATH
    )
    
    # Try to load existing index
    try:
        vector_store.load()
        logger.info("Loaded existing vector store")
    except FileNotFoundError:
        logger.info("No existing vector store found, starting fresh")
    
    # Initialize repository loader
    repo_loader = RepositoryLoader(settings.REPO_CLONE_PATH)
    
    # Initialize ingestion service
    ingestion_service = IngestionService(
        repo_loader=repo_loader,
        embedder=embedder,
        vector_store=vector_store,
        storage_service=storage_service
    )
    logger.info("Ingestion service initialized")
    
    # Initialize LLM client (Groq)
    llm_client = LLMClient(
        api_key=settings.GROQ_API_KEY,
        model=settings.LLM_MODEL,
        temperature=settings.LLM_TEMPERATURE,
        max_tokens=settings.LLM_MAX_TOKENS
    )
    logger.info("Groq LLM client initialized")
    
    # Initialize agent
    agent = CodebaseAgent(
        llm=llm_client,
        vector_store=vector_store,
        metadata_db=database,
        config={
            'include_flow': True,
            'max_flow_depth': settings.MAX_FLOW_DEPTH
        }
    )
    logger.info("Agent initialized")
    
    # Initialize controllers
    repo_controller = RepositoryController(ingestion_service, storage_service)
    query_controller = QueryController(agent, storage_service)
    file_controller = FileController(storage_service)
    
    # Initialize routes with controllers
    init_routes(repo_controller, query_controller, file_controller)
    logger.info("Routes initialized")
    
    yield
    
    # Shutdown
    logger.info("Shutting down AI Codebase Onboarding API")
    # Save vector store
    try:
        vector_store.save()
        logger.info("Vector store saved")
    except Exception as e:
        logger.error(f"Error saving vector store: {e}")


# Create FastAPI application
app = FastAPI(
    title="AI Codebase Onboarding API",
    description="AI-powered developer tool for understanding codebases through natural language queries",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(router)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "name": "AI Codebase Onboarding API",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
