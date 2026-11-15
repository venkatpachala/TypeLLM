from typing import Protocol

# This is the interface, anything that has this method of async def
# can be used as a provider

# this is the Dependency Inversion Principle -
# DIP - High level code depens on abstraction not on HTTP clients

# High-level modules should not depend on low-level modules. 
# Both should depend on abstractions (such as interfaces or abstract 
# classes).

# 1. Define the provider contracr

class Provider(Protocol):
    async def generate(self,prompt:str)-> str:
        ...

# 2. Create configuration and errors

from dataclasses import dataclass

class CapacityExceeded(Exception):
    pass

# we can use this at times of error exceptions like 
# raise CapacityExceeded("TypeLLM is at capacity")

class ProviderDeadlineExceeded(Exception):
    pass

@dataclass(frozen=True, slots=True)
class EngineConfig:
    max_in_flight: int = 3
    admission_timeout: float = 0.05
    execution_timeout: float = 2.0

    def __post_init__(self):
        # It is written in dunder becz that is the special method
        # used for validation
        if self.max_in_flight < 1:
            raise ValueError("max_in_flight must be positive")
        if self.admission_timeout <= 0:
            raise ValueError("admission_timeout must be positive")
        if self.execution_timeout <= 0:
            raise ValueError("execution_timeout must be positive")

# 3. Implement the inference engine

import asyncio

class InferenceEngine:
    def __init__(
        self,
        provider: Provider,
        config: EngineConfig,
    ):
        self._provider = provider
        self._config = config
        self._slots = asyncio.Semaphore(
            config.max_in_flight
        )

    async def generate(self, prompt: str) -> str:
        if not prompt.strip():
            raise ValueError("prompt must not be empty")

        # Phase 1: wait for capacity
        try:
            await asyncio.wait_for(
                self._slots.acquire(),
                timeout=self._config.admission_timeout,
            )

        except TimeoutError as exc:
            raise CapacityExceeded(
                "TypeLLM is at capacity"
            ) from exc

        # Phase 2: execute with a deadline
        try:
            try:
                #async with is the asynchronous counterpart for async 
                # context managers
                async with asyncio.timeout(
                    self._config.execution_timeout):
                    return await self._provider.generate(prompt)

            except TimeoutError as exc:
                raise ProviderDeadlineExceeded(
                    "Provider exceeded deadline"
                ) from exc

        finally:
            # Release the permit on success,
            # errors, or cancellation.
            self._slots.release()


