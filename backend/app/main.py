from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import get_settings
from .database import init_db

settings = get_settings()

# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-powered multi-cloud resource management platform",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    init_db()
    print(f">> {settings.app_name} v{settings.app_version} started")
    print(f">> API Documentation: http://localhost:8000/docs")
    if settings.enable_nl_query:
        print(">> AI Natural Language Query: Enabled")
    if settings.enable_anomaly_detection:
        print(">> AI Anomaly Detection: Enabled")
    if settings.enable_ml_recommendations:
        print(">> ML Recommendations: Enabled")
    if settings.enable_cost_forecasting:
        print(">> Cost Forecasting: Enabled")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "features": {
            "nl_query": settings.enable_nl_query,
            "anomaly_detection": settings.enable_anomaly_detection,
            "ml_recommendations": settings.enable_ml_recommendations,
            "cost_forecasting": settings.enable_cost_forecasting
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "version": settings.app_version
    }


# Import and include routers
from .routers import providers, instances, ai

app.include_router(providers.router, prefix=f"{settings.api_v1_prefix}/providers", tags=["providers"])
app.include_router(instances.router, prefix=f"{settings.api_v1_prefix}/instances", tags=["instances"])
app.include_router(ai.router, prefix=f"{settings.api_v1_prefix}/ai", tags=["ai"])

# TODO: Add these routers as they are implemented
# from .routers import metrics, billing, recommendations
# app.include_router(metrics.router, prefix=f"{settings.api_v1_prefix}/metrics", tags=["metrics"])
# app.include_router(billing.router, prefix=f"{settings.api_v1_prefix}/billing", tags=["billing"])
# app.include_router(recommendations.router, prefix=f"{settings.api_v1_prefix}/recommendations", tags=["recommendations"])
