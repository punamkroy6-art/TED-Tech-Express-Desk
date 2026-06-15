import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger("ted_api")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process the request
        response = await call_next(request)
        
        process_time_ms = (time.time() - start_time) * 1000
        
        # Log request metadata and execution latency
        logger.info(
            f"Method={request.method} Path={request.url.path} "
            f"Status={response.status_code} Latency={process_time_ms:.2f}ms"
        )
        
        return response
