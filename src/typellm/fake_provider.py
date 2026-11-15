import asyncio

class FakeProvider:
    def __init__(self, delay: float = 0.2):
        self.delay = delay
        self.active = 0
        self.peak_active = 0

    async def generate(self, prompt: str) -> str:
        self.active += 1

        self.peak_active = max(
            self.peak_active,
            self.active
        )

        try:
            await asyncio.sleep(self.delay)
            return f"Response: {prompt}"

        finally:
            self.active -= 1
