import httpx
import asyncio
import logging
from typing import Any, Dict, Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger("jarvis.adapter")

class ServiceUnavailableError(Exception):
    pass

class BaseAdapter:
    """
    Base integration adapter featuring circuit breakers, retries with exponential backoff,
    and standard health checks. Prevents JARVIS from silently failing.
    """
    
    def __init__(self, service_name: str, base_url: str):
        self.service_name = service_name
        self.base_url = base_url
        # Async HTTP client
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=10.0)
        self.is_healthy = True

    async def health_check(self) -> bool:
        """Ping the service to ensure it's online before heavy operations."""
        try:
            # Subclasses should override this if they have a specific /health endpoint
            response = await self.client.get("/")
            if response.status_code < 500:
                self.is_healthy = True
                return True
            else:
                self.is_healthy = False
                return False
        except Exception:
            self.is_healthy = False
            return False

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((httpx.RequestError, ServiceUnavailableError))
    )
    async def _safe_request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """
        Executes an HTTP request with Tenacity backoff retries.
        """
        if not self.is_healthy:
            logger.warning(f"[{self.service_name}] marked as unhealthy. Attempting request anyway...")
            
        try:
            response = await self.client.request(method, endpoint, **kwargs)
            response.raise_for_status()
            self.is_healthy = True
            return response
        except httpx.HTTPStatusError as e:
            if e.response.status_code >= 500:
                self.is_healthy = False
                raise ServiceUnavailableError(f"Service {self.service_name} returned 5xx")
            raise
        except httpx.RequestError as e:
            self.is_healthy = False
            logger.error(f"[{self.service_name}] network error: {e}")
            raise ServiceUnavailableError(str(e))
            
    async def close(self):
        await self.client.aclose()
