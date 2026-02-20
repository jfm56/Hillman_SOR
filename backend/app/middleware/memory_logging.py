"""Memory logging middleware for FastAPI.

Logs per-request:
- Token count
- Chunks retrieved
- Image count
- Request memory usage

Throws controlled error if limits exceeded.
"""
import logging
import tracemalloc
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Hard limits
MAX_CHUNKS_PER_REQUEST = 8
MAX_IMAGES_PER_REQUEST = 5
MAX_TOKENS_PER_REQUEST = 6000


class MemoryLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log memory usage and enforce limits."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Start memory tracking
        tracemalloc.start()
        
        # Initialize request state for tracking
        request.state.chunks_retrieved = 0
        request.state.images_processed = 0
        request.state.tokens_used = 0
        
        try:
            response = await call_next(request)
            
            # Get memory stats
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            # Log memory usage for AI-related endpoints
            if "/api/v1/" in request.url.path:
                chunks = getattr(request.state, 'chunks_retrieved', 0)
                images = getattr(request.state, 'images_processed', 0)
                tokens = getattr(request.state, 'tokens_used', 0)
                
                logger.info(
                    f"Request: {request.method} {request.url.path} | "
                    f"Memory: {current / 1024 / 1024:.2f}MB (peak: {peak / 1024 / 1024:.2f}MB) | "
                    f"Chunks: {chunks} | Images: {images} | Tokens: {tokens}"
                )
                
                # Warn if approaching limits
                if chunks > MAX_CHUNKS_PER_REQUEST * 0.8:
                    logger.warning(f"High chunk count: {chunks}")
                if images > MAX_IMAGES_PER_REQUEST * 0.8:
                    logger.warning(f"High image count: {images}")
                if peak > 500 * 1024 * 1024:  # 500MB
                    logger.warning(f"High memory usage: {peak / 1024 / 1024:.2f}MB")
            
            return response
            
        except Exception as e:
            tracemalloc.stop()
            raise


def check_limits(request: Request, chunks: int = 0, images: int = 0, tokens: int = 0):
    """Check and update request limits. Raises error if exceeded."""
    request.state.chunks_retrieved = getattr(request.state, 'chunks_retrieved', 0) + chunks
    request.state.images_processed = getattr(request.state, 'images_processed', 0) + images
    request.state.tokens_used = getattr(request.state, 'tokens_used', 0) + tokens
    
    if request.state.chunks_retrieved > MAX_CHUNKS_PER_REQUEST:
        raise ValueError(f"Chunk limit exceeded: {request.state.chunks_retrieved} > {MAX_CHUNKS_PER_REQUEST}")
    
    if request.state.images_processed > MAX_IMAGES_PER_REQUEST:
        raise ValueError(f"Image limit exceeded: {request.state.images_processed} > {MAX_IMAGES_PER_REQUEST}")
    
    if request.state.tokens_used > MAX_TOKENS_PER_REQUEST:
        raise ValueError(f"Token limit exceeded: {request.state.tokens_used} > {MAX_TOKENS_PER_REQUEST}")
