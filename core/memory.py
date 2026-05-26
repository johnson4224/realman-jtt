from typing import Any, Optional
from datetime import datetime


class SharedMemory:
    def __init__(self, initial_state: Optional[dict] = None):
        self._state: dict = initial_state or {}
        self._history: list[dict] = []
        self._agent_trace: list[str] = []

    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def set(self, key: str, value: Any):
        self._state[key] = value

    def update(self, updates: dict):
        self._state.update(updates)

    def has(self, key: str) -> bool:
        return key in self._state

    def record_event(self, agent_name: str, result: dict):
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "agent": agent_name,
            "result": result,
        })
        self._agent_trace.append(agent_name)

    @property
    def state(self) -> dict:
        return dict(self._state)

    @property
    def history(self) -> list[dict]:
        return list(self._history)

    @property
    def agent_trace(self) -> list[str]:
        return list(self._agent_trace)

    @property
    def visited_agents(self) -> set:
        return set(self._agent_trace)

    def has_been_visited_by(self, agent_name: str) -> bool:
        return agent_name in self._agent_trace

    def __repr__(self):
        return f"SharedMemory(state_keys={list(self._state.keys())}, trace={self._agent_trace})"