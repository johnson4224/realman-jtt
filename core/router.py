from typing import Optional
from .agent import Agent, AgentResult
from .memory import SharedMemory


class AgentRouter:
    def __init__(self):
        self._agents: dict[str, Agent] = {}

    def register(self, agent: Agent):
        self._agents[agent.name] = agent

    def register_many(self, agents: list[Agent]):
        for agent in agents:
            self.register(agent)

    def get(self, name: str) -> Optional[Agent]:
        return self._agents.get(name)

    def resolve_entry(self, state: SharedMemory) -> Optional[Agent]:
        for agent in self._agents.values():
            if agent.can_handle(state):
                return agent
        return None

    @property
    def agent_names(self) -> list[str]:
        return list(self._agents.keys())


class EventLoop:
    def __init__(self, router: AgentRouter, state: SharedMemory, max_steps: int = 20):
        self.router = router
        self.state = state
        self.max_steps = max_steps
        self.results: list[dict] = []

    def run(self, entry_agent_name: Optional[str] = None) -> list[dict]:
        if entry_agent_name:
            current_agent = self.router.get(entry_agent_name)
        else:
            current_agent = self.router.resolve_entry(self.state)

        if current_agent is None:
            print("[EventLoop] 没有Agent可以处理当前任务")
            return self.results

        step = 0
        while current_agent and step < self.max_steps:
            step += 1
            print(f"\n{'='*50}")
            print(f"[Step {step}] 当前Agent: {current_agent.name}")
            print(f"{'='*50}")

            result: AgentResult = current_agent.run(self.state)

            self.state.update(result.state_update)
            self.state.record_event(current_agent.name, {
                "message": result.message,
                "next_agent": result.next_agent,
                "state_update": result.state_update,
            })

            self.results.append({
                "step": step,
                "agent": current_agent.name,
                "message": result.message,
                "next_agent": result.next_agent,
                "state_update": result.state_update,
            })

            print(f"\n[{current_agent.name}] 完整输出:")
            print(result.message)
            if result.next_agent:
                print(f"[{current_agent.name}] Handoff -> {result.next_agent}")

            if result.next_agent is None:
                print(f"\n[EventLoop] 没有更多handoff，流程结束")
                break

            next_agent = self.router.get(result.next_agent)
            if next_agent is None:
                print(f"\n[EventLoop] 目标Agent '{result.next_agent}' 未注册，流程结束")
                break

            if self._detect_loop(next_agent.name):
                print(f"\n[EventLoop] 检测到循环handoff，流程结束")
                break

            current_agent = next_agent

        if step >= self.max_steps:
            print(f"\n[EventLoop] 达到最大步数限制 ({self.max_steps})，强制结束")

        return self.results

    def _detect_loop(self, agent_name: str) -> bool:
        recent = self.state.agent_trace[-5:]
        count = recent.count(agent_name)
        return count >= 3