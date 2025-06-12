import asyncio
import time
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    def __init__(self, calls_per_second: float):
        self.calls_per_second = calls_per_second
        self.min_interval = 1.0 / calls_per_second
        self.last_call_time: Optional[float] = None
        self._lock = asyncio.Lock()

    async def acquire(self):
        async with self._lock:
            if self.last_call_time is not None:
                elapsed = time.time() - self.last_call_time
                if elapsed < self.min_interval:
                    sleep_time = self.min_interval - elapsed
                    logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
                    await asyncio.sleep(sleep_time)
            self.last_call_time = time.time()

class TokenBucketRateLimiter:
    def __init__(self, tokens_per_second: float, bucket_size: int):
        self.tokens_per_second = tokens_per_second
        self.bucket_size = bucket_size
        self.tokens = bucket_size
        self.last_update = time.time()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1):
        async with self._lock:
            now = time.time()
            time_passed = now - self.last_update
            self.tokens = min(
                self.bucket_size,
                self.tokens + time_passed * self.tokens_per_second
            )
            self.last_update = now

            if self.tokens < tokens:
                sleep_time = (tokens - self.tokens) / self.tokens_per_second
                logger.debug(f"Token bucket: sleeping for {sleep_time:.2f}s")
                await asyncio.sleep(sleep_time)
                self.tokens = tokens

            self.tokens -= tokens 