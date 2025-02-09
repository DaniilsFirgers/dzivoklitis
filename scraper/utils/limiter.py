import asyncio
from typing import Callable


class RateLimiterQueue:
    """
    A simple rate limiter that queues requests and executes them at a controlled rate.

    Attributes:
        rate (int): Maximum number of requests allowed per time window.
        per (int): Time window in seconds for the rate limit.
    """

    def __init__(self, rate: int, per: int):
        """
        Initializes the rate limiter.

        Args:
            rate (int): The number of allowed requests.
            per (int): The time window in seconds within which 'rate' requests can be made.
        """
        self.queue: asyncio.Queue = asyncio.Queue()
        self.rate: int = rate
        self.per: int = per
        self._task = None

    def start(self):
        """Starts the rate limiter."""
        if self._task is not None:
            return
        asyncio.create_task(self._worker())

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
            request = await self.queue.get()
            await request()
            await asyncio.sleep((self.per / self.rate) + 0.1)
