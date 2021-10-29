import unittest
from abc import (
    ABC,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
    call,
)
from uuid import (
    uuid4,
)

from minos.common import (
    NULL_UUID,
    Condition,
    MinosSetup,
    MinosSnapshot,
    Ordering,
    Transaction,
)
from minos.common.transactions import (
    TRANSACTION_CONTEXT_VAR,
)
from tests.utils import (
    FakeAsyncIterator,
    FakeSnapshot,
)


class TestMinosSnapshot(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        super().setUp()

        self.snapshot = FakeSnapshot()

        self.synchronize_mock = AsyncMock()
        self.get_mock = AsyncMock(return_value=1)
        self.find_mock = MagicMock(return_value=FakeAsyncIterator(range(5)))

        self.snapshot._get = self.get_mock
        self.snapshot._find = self.find_mock
        self.snapshot._synchronize = self.synchronize_mock

    def test_subclass(self):
        self.assertTrue(issubclass(MinosSnapshot, (ABC, MinosSetup)))

    def test_abstract(self):
        # noinspection PyUnresolvedReferences
        self.assertEqual({"_get", "_find", "_synchronize"}, MinosSnapshot.__abstractmethods__)

    async def test_get(self):
        transaction_uuid = uuid4()
        uuid = uuid4()
        observed = await self.snapshot.get("path.to.Aggregate", uuid, transaction_uuid)
        self.assertEqual(1, observed)

        self.assertEqual(1, self.synchronize_mock.call_count)
        self.assertEqual(call(), self.synchronize_mock.call_args)

        self.assertEqual(1, self.get_mock.call_count)
        args = call(aggregate_name="path.to.Aggregate", uuid=uuid, transaction_uuid=transaction_uuid)
        self.assertEqual(args, self.get_mock.call_args)

    async def test_get_transaction_null(self):
        await self.snapshot.get("path.to.Aggregate", uuid4())

        self.assertEqual(1, self.get_mock.call_count)
        self.assertEqual(NULL_UUID, self.get_mock.call_args.kwargs["transaction_uuid"])

    async def test_get_transaction_context(self):
        transaction = Transaction()
        TRANSACTION_CONTEXT_VAR.set(transaction)
        await self.snapshot.get("path.to.Aggregate", uuid4())

        self.assertEqual(1, self.get_mock.call_count)
        self.assertEqual(transaction.uuid, self.get_mock.call_args.kwargs["transaction_uuid"])

    async def test_find(self):
        transaction_uuid = uuid4()
        iterable = self.snapshot.find(
            "path.to.Aggregate", Condition.TRUE, Ordering.ASC("name"), 10, True, transaction_uuid
        )
        observed = [a async for a in iterable]
        self.assertEqual(list(range(5)), observed)

        self.assertEqual(1, self.synchronize_mock.call_count)
        self.assertEqual(call(), self.synchronize_mock.call_args)

        self.assertEqual(1, self.find_mock.call_count)
        args = call(
            aggregate_name="path.to.Aggregate",
            condition=Condition.TRUE,
            ordering=Ordering.ASC("name"),
            limit=10,
            streaming_mode=True,
            transaction_uuid=transaction_uuid,
        )
        self.assertEqual(args, self.find_mock.call_args)

    async def test_find_transaction_null(self):
        [a async for a in self.snapshot.find("path.to.Aggregate", Condition.TRUE)]

        self.assertEqual(1, self.find_mock.call_count)
        self.assertEqual(NULL_UUID, self.find_mock.call_args.kwargs["transaction_uuid"])

    async def test_find_transaction_context(self):
        transaction = Transaction()
        TRANSACTION_CONTEXT_VAR.set(transaction)
        [a async for a in self.snapshot.find("path.to.Aggregate", Condition.TRUE)]

        self.assertEqual(1, self.find_mock.call_count)
        self.assertEqual(transaction.uuid, self.find_mock.call_args.kwargs["transaction_uuid"])

    async def test_synchronize(self):
        await self.snapshot.synchronize()

        self.assertEqual(1, self.synchronize_mock.call_count)
        self.assertEqual(call(), self.synchronize_mock.call_args)


if __name__ == "__main__":
    unittest.main()
