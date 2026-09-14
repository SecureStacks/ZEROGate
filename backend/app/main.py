from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.database import Base, engine, SessionLocal
import app.models  # Ensures all models are registered with Base metadata
from app.seed.seed_data import seed_database
from app.policy.seed import seed_policies
from app.segmentation.seed import seed_segments, seed_segment_rules
from app.api.health import router as health_router
from app.api.users import router as users_router
from app.api.devices import router as devices_router
from app.api.resources import router as resources_router
from app.api.access_requests import router as access_requests_router
from app.api.demo import router as demo_router
from app.api.risk import router as risk_router
from app.api.pdp import router as pdp_router
from app.api.policies import router as policies_router
from app.api.segmentation import router as segmentation_router
from app.api.mfa import router as mfa_router
from app.api.pep import router as pep_router
from app.api.dashboard import router as dashboard_router
from app.api.logs import router as logs_router
from app.api.topology import router as topology_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize all database tables
    Base.metadata.create_all(bind=engine)
    
    # Run deterministic seed data initialization
    db = SessionLocal()
    try:
        seed_database(db)
        seed_policies(db)
        seed_segments(db)
        seed_segment_rules(db)
    finally:
        db.close()
    
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ZeroGate - Context-Aware Zero Trust Access Simulator (ZTNA) API",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Set up CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Routers under API_V1_STR (/api)
from app.api.auth import router as auth_router

app.include_router(health_router, prefix=settings.API_V1_STR)
app.include_router(health_router, prefix="")
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(users_router, prefix=settings.API_V1_STR)
app.include_router(devices_router, prefix=settings.API_V1_STR)
app.include_router(resources_router, prefix=settings.API_V1_STR)
app.include_router(access_requests_router, prefix=settings.API_V1_STR)
app.include_router(demo_router, prefix=settings.API_V1_STR)
app.include_router(risk_router, prefix=settings.API_V1_STR)
app.include_router(pdp_router, prefix=settings.API_V1_STR)
app.include_router(policies_router, prefix=settings.API_V1_STR)
app.include_router(segmentation_router, prefix=settings.API_V1_STR)
app.include_router(mfa_router, prefix=settings.API_V1_STR)
app.include_router(pep_router, prefix=settings.API_V1_STR)
app.include_router(dashboard_router, prefix=settings.API_V1_STR)
app.include_router(logs_router, prefix=settings.API_V1_STR)
app.include_router(topology_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "online",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
