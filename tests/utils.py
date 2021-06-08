"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""
from pathlib import (
    Path,
)
from typing import (
    Any,
    AsyncIterator,
    NoReturn,
    Optional,
)
from uuid import (
    UUID,
)

from minos.common import (
    CommandReply,
    MinosBroker,
    MinosModel,
    MinosRepository,
    MinosRepositoryEntry,
    MinosSagaManager,
)

BASE_PATH = Path(__file__).parent


class FakeRepository(MinosRepository):
    """For testing purposes."""

    async def _submit(self, entry: MinosRepositoryEntry) -> MinosRepositoryEntry:
        """For testing purposes."""

    async def _select(self, *args, **kwargs) -> AsyncIterator[MinosRepositoryEntry]:
        """For testing purposes."""


class FakeBroker(MinosBroker):
    """For testing purposes."""

    def __init__(self):
        super().__init__()
        self.call_count = 0
        self.calls_kwargs = list()

    async def send(self, items: list[MinosModel], **kwargs) -> NoReturn:
        """For testing purposes."""
        self.call_count += 1
        self.calls_kwargs.append({"items": items} | kwargs)

    @property
    def call_kwargs(self) -> Optional[dict[str, Any]]:
        """For testing purposes."""
        if len(self.calls_kwargs) == 0:
            return None
        return self.calls_kwargs[-1]


class FakeSagaManager(MinosSagaManager):
    """For testing purposes."""

    async def _run_new(self, name: str, **kwargs) -> UUID:
        """For testing purposes."""

    async def _load_and_run(self, reply: CommandReply, **kwargs) -> UUID:
        """For testing purposes."""


class FakeEntrypoint:
    """For testing purposes."""

    def __init__(self):
        self.call_count = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return

    def run_forever(self):
        """For testing purposes."""
        self.call_count += 1
