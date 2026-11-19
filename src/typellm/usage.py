import asyncio

class UsageCounter:
    def __init__(self)-> None:
        self._total=0
        self._lock=asyncio.Lock()

    @property
    def total(self)->int:
        return self._total
    async def record(self, tokens:int)-> None:
        if tokens<0:
            raise ValueError("tokens cannot be negative")
        async with self._lock:
            previous=self._total

            await asyncio.sleep(0)
            self._total=previous+tokens