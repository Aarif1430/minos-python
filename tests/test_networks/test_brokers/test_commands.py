"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""
import unittest
from unittest.mock import (
    AsyncMock,
)
from uuid import (
    uuid4,
)

from minos.common import (
    Command,
)
from minos.common.testing import (
    PostgresAsyncTestCase,
)
from minos.networks import (
    CommandBroker,
)
from tests.utils import (
    BASE_PATH,
    FakeModel,
)


class TestCommandBroker(PostgresAsyncTestCase):
    CONFIG_FILE_PATH = BASE_PATH / "test_config.yml"

    def test_from_config_default(self):
        broker = CommandBroker.from_config(config=self.config)
        self.assertIsInstance(broker, CommandBroker)

    def test_action(self):
        self.assertEqual("command", CommandBroker.ACTION)

    async def test_send(self):
        mock = AsyncMock(return_value=56)
        saga = uuid4()

        async with CommandBroker.from_config(config=self.config) as broker:
            broker.enqueue = mock
            identifier = await broker.send(FakeModel("foo"), "fake", saga, "ekaf")

        self.assertEqual(56, identifier)
        self.assertEqual(1, mock.call_count)

        args = mock.call_args.args
        self.assertEqual("fake", args[0])
        self.assertEqual(Command("fake", FakeModel("foo"), saga, "ekaf"), Command.from_avro_bytes(args[1]))


if __name__ == "__main__":
    unittest.main()
