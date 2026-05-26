from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


@dataclass
class AgentResult:
    message: str
    next_agent: Optional[str] = None
    state_update: dict = field(default_factory=dict)


class Rule(ABC):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description

    @abstractmethod
    def evaluate(self, agent: "Agent", state: "SharedMemory") -> bool:
        pass


class AcceptRule(Rule):
    def __init__(self, condition: Callable[["Agent", "SharedMemory"], bool], name: str = "", description: str = ""):
        super().__init__(name or "accept_rule", description)
        self._condition = condition

    def evaluate(self, agent: "Agent", state: "SharedMemory") -> bool:
        return self._condition(agent, state)


class RejectRule(Rule):
    def __init__(self, condition: Callable[["Agent", "SharedMemory"], bool], name: str = "", description: str = ""):
        super().__init__(name or "reject_rule", description)
        self._condition = condition

    def evaluate(self, agent: "Agent", state: "SharedMemory") -> bool:
        return self._condition(agent, state)


class HandoffRule(Rule):
    def __init__(
        self,
        condition: Callable[["Agent", "SharedMemory"], bool],
        target: Callable[["Agent", "SharedMemory"], Optional[str]],
        name: str = "",
        description: str = "",
    ):
        super().__init__(name or "handoff_rule", description)
        self._condition = condition
        self._target = target

    def evaluate(self, agent: "Agent", state: "SharedMemory") -> bool:
        return self._condition(agent, state)

    def get_target(self, agent: "Agent", state: "SharedMemory") -> Optional[str]:
        return self._target(agent, state)


class Agent(ABC):
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.accept_rules: list[AcceptRule] = []
        self.reject_rules: list[RejectRule] = []
        self.handoff_rules: list[HandoffRule] = []
        self._setup_rules()

    @abstractmethod
    def _setup_rules(self):
        pass

    def can_handle(self, state: "SharedMemory") -> bool:
        for rule in self.reject_rules:
            if rule.evaluate(self, state):
                return False
        for rule in self.accept_rules:
            if not rule.evaluate(self, state):
                return False
        return True

    def decide_handoff(self, state: "SharedMemory") -> Optional[str]:
        for rule in self.handoff_rules:
            if rule.evaluate(self, state):
                return rule.get_target(self, state)
        return None

    @abstractmethod
    def execute(self, state: "SharedMemory") -> AgentResult:
        pass

    def clarify(self, state: "SharedMemory"):
        """在执行前询问用户不清楚的信息。默认什么都不问，Agent可覆盖"""
        pass

    def run(self, state: "SharedMemory") -> AgentResult:
        if not self.can_handle(state):
            return AgentResult(
                message=f"[{self.name}] 无法处理当前任务，跳过",
                next_agent=None,
                state_update={},
            )
        self.clarify(state)
        result = self.execute(state)
        if result.next_agent is None:
            state.update(result.state_update)
            result.next_agent = self.decide_handoff(state)
        return result

    def __repr__(self):
        return f"Agent({self.name})"