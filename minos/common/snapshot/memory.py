"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""
from __future__ import (
    annotations,
)

from typing import (
    TYPE_CHECKING,
    AsyncIterator,
)

from ..exceptions import (
    MinosRepositoryAggregateNotFoundException,
    MinosRepositoryDeletedAggregateException,
)
from ..repository import (
    RepositoryAction,
)
from .abc import (
    MinosSnapshot,
)

if TYPE_CHECKING:
    from ..model import (
        Aggregate,
    )


class InMemorySnapshot(MinosSnapshot):
    """TODO"""

    async def get(self, aggregate_name: str, ids: list[int], **kwargs) -> AsyncIterator[Aggregate]:
        """TODO

        :param aggregate_name: TODO
        :param ids: TODO
        :param kwargs: TODO
        :return: TODO
        """
        iterable = map(lambda aggregate_id: self._get_one(aggregate_name, aggregate_id, **kwargs), ids)

        for item in iterable:
            yield await item

    # noinspection PyShadowingBuiltins
    @staticmethod
    async def _get_one(aggregate_name: str, id: int, _repository, **kwargs) -> Aggregate:
        from operator import (
            attrgetter,
        )

        # noinspection PyTypeChecker
        entries = [v async for v in _repository.select(aggregate_name=aggregate_name, aggregate_id=id)]
        if not len(entries):
            raise MinosRepositoryAggregateNotFoundException(f"Not found any entries for the {repr(id)} id.")

        entry = max(entries, key=attrgetter("version"))
        if entry.action == RepositoryAction.DELETE:
            raise MinosRepositoryDeletedAggregateException(f"The {id} id points to an already deleted aggregate.")
        cls = entry.aggregate_cls
        instance = cls.from_avro_bytes(
            entry.data, id=entry.aggregate_id, version=entry.version, _repository=_repository, **kwargs
        )
        return instance
