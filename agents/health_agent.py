from core.agent import Agent, AgentResult, AcceptRule, RejectRule, HandoffRule
from core.memory import SharedMemory
from tools.llm import ask_llm


class HealthAgent(Agent):
    def __init__(self):
        super().__init__(
            name="HealthAgent",
            description="健康管理助手：分析睡眠和健康目标，给出综合健康建议",
        )

    def _setup_rules(self):
        self.accept_rules = [
            AcceptRule(
                name="poor_sleep_detected",
                description="检测到睡眠时间过晚时接收任务",
                condition=lambda agent, state: (
                    state.has("sleep_time")
                    and "凌晨" in str(state.get("sleep_time", ""))
                ),
            ),
        ]

        self.reject_rules = [
            RejectRule(
                name="already_advised",
                description="如果已经给出健康建议则拒绝",
                condition=lambda agent, state: state.has("health_done"),
            ),
            RejectRule(
                name="sleep_is_fine",
                description="睡眠时间正常时拒绝任务",
                condition=lambda agent, state: (
                    not state.has("sleep_time")
                    or "凌晨" not in str(state.get("sleep_time", ""))
                ),
            ),
        ]

        self.handoff_rules = [
            HandoffRule(
                name="end_workflow",
                description="健康建议完成，流程结束",
                condition=lambda agent, state: True,
                target=lambda agent, state: None,
            ),
        ]

    def execute(self, state: SharedMemory) -> AgentResult:
        system_prompt = """
你是健康管理助手。
负责：
- 分析用户睡眠习惯
- 结合健康目标给出建议
- 提醒作息调整
"""

        user_prompt = f"""
用户健康目标：
{state.get("health_goal")}

用户睡眠时间：
{state.get("sleep_time")}

用户日程分析：
{state.get("calendar_analysis", "")}

饮食计划：
{state.get("meal_plan", "")}

请给出：
1. 睡眠改善建议
2. 作息调整方案
3. 综合健康提醒
"""

        if state.has("user_feedback"):
            user_prompt += f"\n用户反馈（请参考）：{state.get('user_feedback')}\n"

        advice = ask_llm(system_prompt, user_prompt)

        return AgentResult(
            message=advice,
            state_update={
                "health_advice": advice,
                "health_done": True,
            },
        )