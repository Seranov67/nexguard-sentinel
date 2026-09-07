import pytest

from sentinel.config import Settings
from sentinel.executor import Executor
from sentinel.policy import Policy
from sentinel.store import StateStore
from sentinel.tests.test_action_loop import GUARDIAN, VAULT, FakeChain, event


@pytest.fixture
def setup(tmp_path):
    settings = Settings(
        "https://rpc.example", "https://graph.example", GUARDIAN, VAULT, tmp_path / "state.sqlite3"
    )
    store = StateStore(settings.state_path)
    chain = FakeChain(store)
    policy = Policy(GUARDIAN, VAULT)
    executor = Executor(settings, store, chain, policy, timeout=0)
    ev = event()
    store.ingest(f"84532:{VAULT}", ev.id, ev.sequence, ev.block, ev.payload())
    return settings, store, chain, executor, ev
