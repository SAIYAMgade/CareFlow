import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from .core.config import settings
from .core.logging import logger
from .core.exceptions import CareFlowException, careflow_exception_handler, general_exception_handler
from .db.init_db import init_database

# Routers
from .api.patients import router as patients_router
from .api.appointments import router as appointments_router
from .api.encounters import router as encounters_router
from .api.observations import router as observations_router
from .api.orders import router as orders_router
from .api.results import router as results_router
from .api.reports import router as reports_router
from .api.data_quality import router as data_quality_router
from .api.audit import router as audit_router
from .api.health import router as health_router
from .api.dashboard import router as dashboard_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting CareFlow API in {settings.ENVIRONMENT_NAME}")
    try:
        init_database()
        logger.info("Database verified on startup.")
    except Exception as e:
        logger.warning(f"Database auto-init on startup skipped or failed: {e}")
    yield
    logger.info("CareFlow API shutting down.")

app = FastAPI(
    title="CareFlow Healthcare Operations API",
    description="Simulated clinical operations, workflow tracking, and reporting platform powered by Oracle Database Free / Standalone Engine.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS Configuration
origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handlers
app.add_exception_handler(CareFlowException, careflow_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include API Routers
api_prefix = settings.API_PREFIX
app.include_router(dashboard_router, prefix=api_prefix)
app.include_router(patients_router, prefix=api_prefix)
app.include_router(appointments_router, prefix=api_prefix)
app.include_router(encounters_router, prefix=api_prefix)
app.include_router(observations_router, prefix=api_prefix)
app.include_router(orders_router, prefix=api_prefix)
app.include_router(results_router, prefix=api_prefix)
app.include_router(reports_router, prefix=api_prefix)
app.include_router(data_quality_router, prefix=api_prefix)
app.include_router(audit_router, prefix=api_prefix)
app.include_router(health_router, prefix=api_prefix)

# Mount Frontend SPA if built
frontend_dist = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../frontend/dist"))
if os.path.exists(frontend_dist):
    app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dist, "assets")), name="assets")

    @app.get("/{full_path:path}")
    def serve_spa(full_path: str):
        if full_path.startswith("api/") or full_path in ("docs", "redoc", "openapi.json"):
            return None
        index_file = os.path.join(frontend_dist, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)
        return {"name": "CareFlow Healthcare Operations Platform", "status": "ONLINE"}
else:
    @app.get("/")
    def root():
        return {
            "name": "CareFlow Healthcare Operations Platform",
            "status": "ONLINE",
            "docs": "/docs",
            "environment": settings.ENVIRONMENT_NAME
        }
