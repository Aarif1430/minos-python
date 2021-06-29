import asyncio
import datetime
import unittest
from collections import (
    namedtuple,
)

import aiopg

from minos.common import (
    Command,
)
from minos.common.testing import (
    PostgresAsyncTestCase,
)
from minos.networks import (
    CommandHandler,
)
from tests.utils import (
    BASE_PATH,
    FakeBroker,
    FakeModel,
)


class TestCommandHandler(PostgresAsyncTestCase):
    CONFIG_FILE_PATH = BASE_PATH / "test_config.yml"

    def test_from_config(self):
        dispatcher = CommandHandler.from_config(config=self.config)
        self.assertIsInstance(dispatcher, CommandHandler)

    async def test_dispatch(self):
        model = FakeModel("foo")
        instance = Command(
            topic="AddOrder", model=model.classname, items=[], saga_uuid="43434jhij", reply_topic="UpdateTicket",
        )

        broker = FakeBroker()

        async with CommandHandler.from_config(config=self.config, broker=broker) as handler:
            queue_id = await self._insert_one(instance)
            await handler.dispatch()
            self.assertTrue(await self._is_processed(queue_id))

        self.assertEqual(1, broker.call_count)
        self.assertEqual(["add_order"], broker.items)
        self.assertEqual("UpdateTicket", broker.topic)
        self.assertEqual("43434jhij", broker.saga_uuid)
        self.assertEqual(None, broker.reply_topic)

    async def test_dispatch_without_reply(self):
        model = FakeModel("foo")
        instance = Command(topic="AddOrder", model=model.classname, items=[], saga_uuid="43434jhij",)

        broker = FakeBroker()

        async with CommandHandler.from_config(config=self.config, broker=broker) as handler:
            queue_id = await self._insert_one(instance)
            await handler.dispatch()
            self.assertTrue(await self._is_processed(queue_id))

        self.assertEqual(0, broker.call_count)

    async def test_dispatch_wrong(self):
        instance = namedtuple("FakeCommand", ("topic", "avro_bytes"))("AddOrder", bytes(b"Test"))

        async with CommandHandler.from_config(config=self.config) as handler:
            queue_id = await self._insert_one(instance)
            await handler.dispatch()
            self.assertFalse(await self._is_processed(queue_id))

    async def _insert_one(self, instance):
        async with aiopg.connect(**self.commands_queue_db) as connect:
            async with connect.cursor() as cur:
                await cur.execute(
                    "INSERT INTO command_queue (topic, partition_id, binary_data, creation_date) "
                    "VALUES (%s, %s, %s, %s) "
                    "RETURNING id;",
                    (instance.topic, 0, instance.avro_bytes, datetime.datetime.now(),),
                )
                return (await cur.fetchone())[0]

    async def _is_processed(self, queue_id):
        async with aiopg.connect(**self.commands_queue_db) as connect:
            async with connect.cursor() as cur:
                await cur.execute("SELECT COUNT(*) FROM command_queue WHERE id=%d" % (queue_id,))
                return (await cur.fetchone())[0] == 0

    async def test_dispatch_concurrent(self):
        model = FakeModel("foo")
        instance = Command(
            topic="AddOrder", model=model.classname, items=[], saga_uuid="43434jhij", reply_topic="UpdateTicket",
        )
        bin_data = instance.avro_bytes

        broker = FakeBroker()
        bin_data_wrong = bytes(b"Test")

        async with CommandHandler.from_config(config=self.config, broker=broker) as handler:
            async with aiopg.connect(**self.commands_queue_db) as connect:
                async with connect.cursor() as cur:
                    for x in range(0, 25):
                        await cur.execute(
                            "INSERT INTO command_queue (topic, partition_id, binary_data, creation_date) "
                            "VALUES (%s, %s, %s, %s) "
                            "RETURNING id;",
                            (instance.topic, 0, bin_data, datetime.datetime.now(),),
                        )
                        await cur.execute(
                            "INSERT INTO command_queue (topic, partition_id, binary_data, creation_date) "
                            "VALUES (%s, %s, %s, %s) "
                            "RETURNING id;",
                            (instance.topic, 0, bin_data_wrong, datetime.datetime.now(),),
                        )

            async with aiopg.connect(**self.commands_queue_db) as connect:
                async with connect.cursor() as cur:
                    await cur.execute("SELECT COUNT(*) FROM command_queue")
                    records = await cur.fetchone()

            assert records[0] == 50

            await asyncio.gather(*[handler.dispatch() for i in range(0, 6)])

            async with aiopg.connect(**self.commands_queue_db) as connect:
                async with connect.cursor() as cur:
                    await cur.execute("SELECT COUNT(*) FROM command_queue")
                    records = await cur.fetchone()

            assert records[0] == 25


if __name__ == "__main__":
    unittest.main()
