from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from contextlib import asynccontextmanager
import logging
from typing import AsyncGenerator

from ..infrastructure.db import get_database_connection, DatabaseConnection
from ..infrastructure.db.repositories import (
    SQLAlchemyTaskRepository,
    SQLAlchemyWorkerRepository, 
    SQLAlchemyTaskResultRepository
)
from ..domain.services.worker_dispatcher_impl import WorkerDispatcherImpl
from ..domain.services.worker_management_impl import WorkerManagementImpl
from ..infrastructure.exceptions import (
    DomainException,
    InfrastructureException,
    PresentationException
)


# Global dependencies
db_connection: DatabaseConnection = None
task_repository: SQLAlchemyTaskRepository = None
worker_repository: SQLAlchemyWorkerRepository = None
result_repository: SQLAlchemyTaskResultRepository = None
dispatcher_service: WorkerDispatcherImpl = None
worker_management_service: WorkerManagementImpl = None


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan management"""
    global db_connection, task_repository, worker_repository, result_repository
    global dispatcher_service, worker_management_service
    
    # Startup
    logging.info("Starting up Worker Dispatcher application...")
    
    # Initialize database connection
    db_connection = get_database_connection()
    await db_connection.create_tables()
    
    # Initialize repositories
    session = db_connection.get_session()
    task_repository = SQLAlchemyTaskRepository(session)
    worker_repository = SQLAlchemyWorkerRepository(session)
    result_repository = SQLAlchemyTaskResultRepository(session)
    
    # Initialize services
    worker_management_service = WorkerManagementImpl(worker_repository)
    dispatcher_service = WorkerDispatcherImpl(
        task_repository,
        worker_repository,
        result_repository,
        worker_management_service
    )
    
    logging.info("Worker Dispatcher application started successfully")
    
    yield
    
    # Shutdown
    logging.info("Shutting down Worker Dispatcher application...")
    if db_connection:
        await db_connection.close()
    logging.info("Worker Dispatcher application shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="Worker Dispatcher API",
        description="A DDD/Clean Architecture FastAPI template with Worker-Dispatcher pattern",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Add middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(GZipMiddleware, minimum_size=1000)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Exception handlers
    @app.exception_handler(DomainException)
    async def domain_exception_handler(request, exc):
        raise HTTPException(status_code=400, detail=str(exc))
    
    @app.exception_handler(InfrastructureException)
    async def infrastructure_exception_handler(request, exc):
        raise HTTPException(status_code=500, detail="Internal server error")
    
    @app.exception_handler(PresentationException)
    async def presentation_exception_handler(request, exc):
        raise HTTPException(status_code=422, detail=str(exc))
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "healthy", "service": "worker-dispatcher"}
    
    # Include routers
    from .logic.task_routes import router as task_router
    from .logic.worker_routes import router as worker_router
    from .logic.monitoring_routes import router as monitoring_router
    from .logic.dispatch_routes import router as dispatch_router
    from .logic.work_routes import router as work_router
    
    app.include_router(task_router, prefix="/api/v1/tasks", tags=["tasks"])
    app.include_router(worker_router, prefix="/api/v1/workers", tags=["workers"])
    app.include_router(monitoring_router, prefix="/api/v1/monitoring", tags=["monitoring"])
    app.include_router(dispatch_router, prefix="/dispatch", tags=["dispatch"])
    app.include_router(work_router, prefix="/work", tags=["work"])
    
    return app


# Dependency injection
def get_dispatcher_service() -> WorkerDispatcherImpl:
    if dispatcher_service is None:
        raise HTTPException(status_code=500, detail="Dispatcher service not initialized")
    return dispatcher_service


def get_worker_management_service() -> WorkerManagementImpl:
    if worker_management_service is None:
        raise HTTPException(status_code=500, detail="Worker management service not initialized")
    return worker_management_service


def get_task_repository() -> SQLAlchemyTaskRepository:
    if task_repository is None:
        raise HTTPException(status_code=500, detail="Task repository not initialized")
    return task_repository


def get_worker_repository() -> SQLAlchemyWorkerRepository:
    if worker_repository is None:
        raise HTTPException(status_code=500, detail="Worker repository not initialized")
    return worker_repository


def get_result_repository() -> SQLAlchemyTaskResultRepository:
    if result_repository is None:
        raise HTTPException(status_code=500, detail="Result repository not initialized")
    return result_repository


# Create the application instance
app = create_app()