"""
Vercel serverless entry point for TED FastAPI backend.
All /api/* requests are routed here by vercel.json.
"""
import sys
import os

# Add backend to path
_backend = os.path.join(os.path.dirname(__file__), '..', 'ted', 'backend')
sys.path.insert(0, os.path.abspath(_backend))

# Force local mock mode on Vercel (no Postgres/Redis needed)
os.environ.setdefault('USE_LOCAL_MOCK', 'true')
os.environ.setdefault('DATABASE_URL', 'sqlite+aiosqlite:////tmp/ted.db')
os.environ.setdefault('REDIS_URL', 'redis://localhost:6379/0')
os.environ.setdefault('JWT_ALGORITHM', 'HS256')
os.environ.setdefault('JWT_EXPIRY_MINUTES', '60')

# JWT secret — override via Vercel environment variable
os.environ.setdefault(
    'JWT_SECRET',
    os.environ.get('JWT_SECRET', 'vercel-demo-secret-change-in-production')
)

# Import the FastAPI app
from app.main import app  # noqa: E402

# Vercel expects the ASGI app to be exported as `app`
__all__ = ['app']
