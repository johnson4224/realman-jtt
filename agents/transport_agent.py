from core.agent import Agent, AgentResult, AcceptRule, RejectRule, HandoffRule
from core.memory import SharedMemory
from tools.llm import ask_llm


class TransportAgent(Agent):
    def __init__(self):
        super().__init__(
            name="TransportAgent",
            description="出行助手：根据天气和日程推荐交通方式",
        )

    def _setup_rules(self):
        self.accept_rules = [
            AcceptRule(
                name="bad_weather_detected",
                description="只有天气包含雨时才接收任务",
                condition=lambda agent, state: (
                    state.get("weather_contains_rain", False) is True
                ),
            ),
        ]

        self.reject_rules = [
            RejectRule(
                name="already_recommended",
                description="如果已经推荐过交通方式则拒绝",
                condition=lambda agent, state: state.has("transport_done"),
            ),
            RejectRule(
                name="no_bad_weather",
                description="天气良好时不需要交通建议，拒绝任务",
                condition=lambda agent, state: (
                    not state.get("weather_contains_rain", False)
                ),
            ),
        ]

        self.handoff_rules = [
            HandoffRule(
                name="handoff_to_food",
                description="交通建议完成后，handoff给FoodAgent",
                condition=lambda agent, state: True,
                target=lambda agent, state: "FoodAgent",
            ),
        ]

    def execute(self, state: SharedMemory) -> AgentResult:
        weather_data = state.get("weather_data", {})
        calendar_analysis = state.get("calendar_analysis", "")
        go_out = state.get("go_out", "")

        system_prompt = """
你是出行助手。
负责：
- 根据天气推荐交通方式
- 建议是否提前出门
规则：
- 只根据用户已提供的信息做规划
- 不要反问用户问题，信息不够就按已知的最佳推测处理
- 直接输出建议，不要提问
"""

        user_prompt = f"""
当前天气：
{weather_data}

用户出行说明：
{go_out}

用户日程分析：
{calendar_analysis}

请推荐：
1. 出行方式（根据用户实际出行场景推荐，比如在校园内步行即可）
2. 是否需要提前出门
3. 需要携带什么（如雨伞）
"""

        if state.has("user_feedback"):
            user_prompt += f"\n用户反馈（请参考）：{state.get('user_feedback')}\n"

        recommendation = ask_llm(system_prompt, user_prompt)

        return AgentResult(
            message=recommendation,
            state_update={
                "transport_recommendation": recommendation,
                "transport_done": True,
            },
        )