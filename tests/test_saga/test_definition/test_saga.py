# Copyright (C) 2020 Clariteia SL
#
# This file is part of minos framework.
#
# Minos framework can not be copied and/or distributed without the express
# permission of Clariteia SL.

import unittest
from shutil import (
    rmtree,
)

from minos.saga import (
    MinosAlreadyOnSagaException,
    MinosSagaException,
    Saga,
    SagaExecution,
    SagaStep,
)
from tests.callbacks import (
    create_ticket_on_reply_callback,
    d_callback,
    e_callback,
    f_callback,
)
from tests.utils import (
    BASE_PATH,
)


class TestSaga(unittest.TestCase):
    DB_PATH = BASE_PATH / "test_db.lmdb"

    def tearDown(self) -> None:
        rmtree(self.DB_PATH, ignore_errors=True)

    def test_empty_step_must_throw_exception(self):
        with self.assertRaises(MinosSagaException) as exc:
            (
                Saga("OrdersAdd2")
                .step()
                .invoke_participant("CreateOrder")
                .with_compensation("DeleteOrder")
                .with_compensation("DeleteOrder2")
                .step()
                .step()
                .invoke_participant("CreateTicket")
                .on_reply(create_ticket_on_reply_callback)
                .step()
                .invoke_participant("VerifyConsumer")
                .commit()
            )

            self.assertEqual("A 'SagaStep' can only define one 'with_compensation' method.", str(exc))

    def test_wrong_step_action_must_throw_exception(self):
        with self.assertRaises(MinosSagaException) as exc:
            (
                Saga("OrdersAdd3")
                .step()
                .invoke_participant("CreateOrder")
                .with_compensation("DeleteOrder")
                .with_compensation("DeleteOrder2")
                .step()
                .on_reply(create_ticket_on_reply_callback)
                .step()
                .invoke_participant("VerifyConsumer")
                .commit()
            )

            self.assertEqual("A 'SagaStep' can only define one 'with_compensation' method.", str(exc))

    def test_build_execution(self):
        saga = Saga("OrdersAdd3").step().invoke_participant("CreateOrder").with_compensation("DeleteOrder").commit()
        execution = saga.build_execution()
        self.assertIsInstance(execution, SagaExecution)

    def test_add_step(self):
        step = SagaStep().invoke_participant("CreateOrder")
        saga = Saga("OrdersAdd3").step(step).commit()

        self.assertEqual([step], saga.steps)

    def test_add_step_raises(self):

        step = SagaStep(Saga("FooTest")).invoke_participant("CreateOrder")
        with self.assertRaises(MinosAlreadyOnSagaException):
            Saga("BarAdd").step(step)


if __name__ == "__main__":
    unittest.main()
