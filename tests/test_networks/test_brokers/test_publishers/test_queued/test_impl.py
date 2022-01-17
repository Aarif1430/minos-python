import unittest
from contextlib import (
    suppress,
)
from unittest.mock import (
    AsyncMock,
    MagicMock,
    call,
)

from minos.networks import (
    BrokerMessageV1,
    BrokerMessageV1Payload,
    BrokerPublisher,
    InMemoryBrokerPublisher,
    InMemoryBrokerPublisherRepository,
    QueuedBrokerPublisher,
)
from tests.utils import (
    FakeAsyncIterator,
)


class TestQueuedBrokerPublisher(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        self.impl = InMemoryBrokerPublisher()
        self.repository = InMemoryBrokerPublisherRepository()

    def test_is_subclass(self):
        self.assertTrue(issubclass(QueuedBrokerPublisher, BrokerPublisher))

    def test_impl(self):
        publisher = QueuedBrokerPublisher(self.impl, self.repository)
        self.assertEqual(self.impl, publisher.impl)

    def test_repository(self):
        publisher = QueuedBrokerPublisher(self.impl, self.repository)
        self.assertEqual(self.repository, publisher.repository)

    async def test_send(self):
        repository_enqueue_mock = AsyncMock()
        self.repository.enqueue = repository_enqueue_mock

        publisher = QueuedBrokerPublisher(self.impl, self.repository)
        message = BrokerMessageV1("foo", BrokerMessageV1Payload("bar"))
        await publisher.send(message)

        self.assertEqual([call(message)], repository_enqueue_mock.call_args_list)

    async def test_run(self):
        messages = [
            BrokerMessageV1("foo", BrokerMessageV1Payload("bar")),
            BrokerMessageV1("bar", BrokerMessageV1Payload("foo")),
        ]

        repository_dequeue_mock = MagicMock(side_effect=[FakeAsyncIterator(messages), InterruptedError])
        self.repository.dequeue_all = repository_dequeue_mock

        impl_send_mock = AsyncMock()
        self.impl.send = impl_send_mock

        publisher = QueuedBrokerPublisher(self.impl, self.repository)

        with suppress(InterruptedError):
            await publisher.run()

        self.assertEqual([call(), call()], repository_dequeue_mock.call_args_list)
        self.assertEqual([call(messages[0]), call(messages[1])], impl_send_mock.call_args_list)


if __name__ == "__main__":
    unittest.main()
