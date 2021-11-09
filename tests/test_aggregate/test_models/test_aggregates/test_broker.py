import unittest
from typing import (
    Optional,
)

from minos.aggregate import (
    Action,
    AggregateDiff,
    FieldDiff,
    FieldDiffContainer,
    ModelRef,
)
from tests.utils import (
    Car,
    MinosTestCase,
    Owner,
)


class TestAggregate(MinosTestCase):
    async def test_create(self):
        car = await Car.create(doors=3, color="blue")

        self.assertEqual(
            [
                {
                    "data": AggregateDiff(
                        uuid=car.uuid,
                        name=Car.classname,
                        version=1,
                        action=Action.CREATE,
                        created_at=car.created_at,
                        fields_diff=FieldDiffContainer(
                            [
                                FieldDiff("doors", int, 3),
                                FieldDiff("color", str, "blue"),
                                FieldDiff("owner", Optional[list[ModelRef[Owner]]], None),
                            ]
                        ),
                    ),
                    "topic": "CarCreated",
                }
            ],
            self.event_broker.calls_kwargs,
        )

    async def test_update(self):
        car = await Car.create(doors=3, color="blue")
        self.event_broker.reset_mock()

        await car.update(color="red")

        self.assertEqual(
            [
                {
                    "data": AggregateDiff(
                        uuid=car.uuid,
                        name=Car.classname,
                        version=2,
                        action=Action.UPDATE,
                        created_at=car.updated_at,
                        fields_diff=FieldDiffContainer([FieldDiff("color", str, "red")]),
                    ),
                    "topic": "CarUpdated",
                },
                {
                    "data": AggregateDiff(
                        uuid=car.uuid,
                        name=Car.classname,
                        version=2,
                        action=Action.UPDATE,
                        created_at=car.updated_at,
                        fields_diff=FieldDiffContainer([FieldDiff("color", str, "red")]),
                    ),
                    "topic": "CarUpdated.color",
                },
            ],
            self.event_broker.calls_kwargs,
        )

    async def test_delete(self):

        car = await Car.create(doors=3, color="blue")
        self.event_broker.reset_mock()

        await car.delete()

        self.assertEqual(
            [
                {
                    "data": AggregateDiff(
                        uuid=car.uuid,
                        name=Car.classname,
                        version=2,
                        action=Action.DELETE,
                        created_at=car.updated_at,
                        fields_diff=FieldDiffContainer.empty(),
                    ),
                    "topic": "CarDeleted",
                }
            ],
            self.event_broker.calls_kwargs,
        )


if __name__ == "__main__":
    unittest.main()
