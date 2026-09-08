"""One bounded runtime tick; classifier is injected by ES401."""

from collections.abc import Callable

from sentinel.executor import Executor
from sentinel.graph import GraphSource
from sentinel.models import Proposal, Withdrawal


class Runtime:
    def __init__(
        self,
        source: GraphSource,
        executor: Executor,
        classify: Callable[[list[Withdrawal]], Proposal | None],
    ) -> None:
        self.source, self.executor, self.classify = source, executor, classify
        self.executor.recover_startup()

    def tick(self) -> str | None:
        if self.executor.store.is_latched():
            return None
        self.source.poll(self.executor.chain.head())
        events = self.executor.store.pending_events(self.source.source)
        if not events:
            return None
        withdrawals = [event for event in events if isinstance(event, Withdrawal)]
        if len(withdrawals) != len(events):
            raise ValueError("Runtime source returned a noncanonical event representation")
        proposal = self.classify(withdrawals)
        if proposal is None:
            return None
        return self.executor.act(withdrawals, proposal)
