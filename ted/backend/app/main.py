import sys
import os
# Ensure backend directory is in sys.path to resolve 'app' imports correctly
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import auth, diagnose, ocr, ticket, loaner, health, autofix, diagnostic
from app.middleware.logging import RequestLoggingMiddleware
from app.database import init_db

# Initialize slowapi rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="TED API",
    description="Tech Express Desk — AI IT Support Kiosk",
    version="1.0.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Enable CORS for frontend UI requests
app.add_middleware(CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4173",
        "http://localhost:5173",
        "https://ted-tech-express-desk.vercel.app",
        "https://*.vercel.app",   # preview deployments
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

# Custom request latency and HTTP status logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(auth,     prefix='/api/auth',    tags=['Auth'])
app.include_router(diagnose, prefix='/api',         tags=['Diagnose'])
app.include_router(ocr,      prefix='/api',         tags=['OCR'])
app.include_router(ticket,   prefix='/api',         tags=['Ticket'])
app.include_router(loaner,   prefix='/api',         tags=['Loaner'])
app.include_router(health,   prefix='/api',         tags=['Health'])
app.include_router(autofix,     prefix='/api',         tags=['AutoFix'])
app.include_router(diagnostic,  prefix='/api',         tags=['Diagnostic'])

# Auto-generate Prometheus metrics configuration
Instrumentator().instrument(app).expose(app)

# Startup hook to initialize the PostgreSQL database schema
@app.on_event('startup')
async def startup():
    await init_db()
