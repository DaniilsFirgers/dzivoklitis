import asyncio
from typing import Callable

from scraper.utils.logger import logger


class RateLimiterQueue:
    """
    A simple rate limiter that queues requests and executes them at a controlled rate.

    Attributes:
        rate (int): Maximum number of requests allowed per time window.
        per (int): Time window in seconds for the rate limit.
    """

    def __init__(self, rate: int, per: int, buffer: float = 0.1):
        """
        Initializes the rate limiter.

        Args:
            rate (int): The number of allowed requests.
            per (int): The time window in seconds within which 'rate' requests can be made.
        """
        self.queue: asyncio.Queue = asyncio.Queue()
        self.rate: int = rate
        self.per: int = per
        self.buffer: float = buffer
        self._task = None

    def start(self):
        """Starts the rate limiter."""
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._worker())

    async def add_request(self, request: Callable[[], asyncio.Future]):
        """
        Adds a request function to the queue.

        Args:
            request (Callable[[], asyncio.Future]): An async function representing the request.
        """

        await self.queue.put(request)

    async def _worker(self):
        """Background worker that processes requests from the queue at a controlled rate."""
        while True:
            try:
                request = await self.queue.get()
                await request()
            except Exception as e:
                logger.error(f"Failed to send message inside worker: {e}")
            finally:
                await asyncio.sleep((self.per / self.rate) + self.buffer)
