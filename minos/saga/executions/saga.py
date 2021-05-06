"""
Copyright (C) 2021 Clariteia SL

This file is part of minos framework.

Minos framework can not be copied and/or distributed without the express permission of Clariteia SL.
"""
from typing import (
    NoReturn,
)
from uuid import (
    UUID,
    uuid4,
)

from ..definitions import (
    Saga,
    SagaStep,
)
from ..exceptions import (
    MinosSagaFailedExecutionStepException,
    MinosSagaPausedExecutionStepException,
)
from ..storage import (
    MinosSagaStorage,
)
from .context import (
    SagaContext,
)
from .status import (
    SagaStatus,
)
from .step import (
    SagaExecutionStep,
)


class SagaExecution(object):
    """TODO"""

    def __init__(
        self, definition: Saga, uuid: UUID, steps: [SagaExecutionStep], context: SagaContext, status: SagaStatus
    ):
        self.uuid = uuid
        self.definition = definition
        self.executed_steps = steps
        # self.context = context  # FIXME
        self.context = ""
        self.status = status
        self.already_rollback = False

    @classmethod
    def from_saga(cls, definition: Saga):
        """TODO

        :param definition: TODO
        :return: TODO
        """
        return cls(definition, uuid=uuid4(), steps=list(), context=SagaContext(), status=SagaStatus.Created)

    def execute(self, step_manager: MinosSagaStorage):
        """TODO

        :param step_manager: TODO
        :return: TODO
        """
        self.status = SagaStatus.Running
        for step in self.pending_steps:
            execution_step = SagaExecutionStep(self, step)
            try:
                self.context = execution_step.execute(self.context, step_manager)
            except MinosSagaFailedExecutionStepException:  # FIXME: Exception that rollbacks execution.
                self.rollback(step_manager)
                self.status = SagaStatus.Errored
                return self
            except MinosSagaPausedExecutionStepException:  # FIXME: Exception that pauses execution.
                self.status = SagaStatus.Paused
                return self
            finally:
                self._add_executed(execution_step)

        self.status = SagaStatus.Finished

    def rollback(self, step_manager: MinosSagaStorage) -> NoReturn:
        """TODO

        :param step_manager: TODO
        :return: TODO
        """

        if self.already_rollback:
            return

        for execution_step in reversed(self.executed_steps):
            self.context = execution_step.rollback(self.context, step_manager)

        self.already_rollback = True

    @property
    def pending_steps(self) -> [SagaStep]:
        """TODO

        :return: TODO
        """
        return self.definition.steps[len(self.executed_steps) :]

    def _add_executed(self, executed_step: SagaExecutionStep):
        """TODO

        :param executed_step: TODO
        :return: TODO
        """
        self.executed_steps.append(executed_step)
