from types import SimpleNamespace

import pytest
from langgraph.checkpoint.memory import MemorySaver

from app.modules.chat.rag import checkpointer


@pytest.mark.asyncio
async def test_memory_backend_uses_in_process_saver(monkeypatch: pytest.MonkeyPatch) -> None:
    await checkpointer.close_checkpointer()
    monkeypatch.setattr(
        checkpointer,
        "get_settings",
        lambda: SimpleNamespace(
            database_enabled=False,
            persistence_backend="memory",
            database_url="unused",
        ),
    )

    saver = await checkpointer.init_checkpointer()

    try:
        assert isinstance(saver, MemorySaver)
        assert checkpointer.get_checkpointer() is saver
    finally:
        await checkpointer.close_checkpointer()
