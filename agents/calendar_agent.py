from core.agent import Agent, AgentResult, AcceptRule, RejectRule, HandoffRule
from core.memory import SharedMemory
from core.ask import ask
from tools.llm import ask_llm


class CalendarAgent(Agent):
    def __init__(self):
        super().__init__(
            name="CalendarAgent",
            description="日程规划助手：分析用户日程，判断时间冲突，给出合理安排建议",
        )

    def _setup_rules(self):
        self.accept_rules = [
            AcceptRule(
                name="has_calendar_data",
                description="state中存在calendar数据时接收任务",
                condition=lambda agent, state: state.has("calendar"),
            ),
        ]

        self.reject_rules = [
            RejectRule(
                name="already_analyzed",
                description="如果calendar已经被分析过则拒绝",
                condition=lambda agent, state: state.has("calendar_analysis_done"),
            ),
        ]

        self.handoff_rules = [
            HandoffRule(
                name="handoff_to_weather",
                description="日程分析完成后，handoff给WeatherAgent检查天气",
                condition=lambda agent, state: True,
                target=lambda agent, state: "WeatherAgent",
            ),
        ]

    def clarify(self, state: SharedMemory):
        calendar = state.get("calendar", "")

        # 1. 如果提到了运动/活动但没给时间
        for activity in ["跑步", "打球", "羽毛球", "篮球", "足球", "健身", "游泳", "运动"]:
            if activity in calendar and not state.has("activity_time"):
                act_time = ask(f"\n[{self.name}] 你提到会{activity}，打算安排在几点？ ").strip()
                state.set("activity_time", act_time)
                break

        # 2. 如果没提到起床时间
        if not any(kw in calendar for kw in ["起床", "几点起", "点起", "醒"]):
            wake = ask(f"[{self.name}] 你明天打算几点起床？ ").strip()
            state.set("wake_time", wake)

    def execute(self, state: SharedMemory) -> AgentResult:
        system_prompt = """
你是日程规划助手。
负责：
- 分析用户日程
- 判断时间冲突
- 给出合理安排建议
规则：
- 只根据用户已提供的信息做规划
- 不要反问用户问题，信息不够就按已知的最佳推测处理
- 直接输出规划结果，不要提问
"""

        extra = ""
        if state.has("activity_time"):
            extra += f"\n运动时间：{state.get('activity_time')}"
        if state.has("wake_time"):
            extra += f"\n起床时间：{state.get('wake_time')}"
        if state.has("user_feedback"):
            extra += f"\n用户反馈（请根据此反馈调整方案）：{state.get('user_feedback')}"

        user_prompt = f"""
用户日程：
{state.get("calendar")}

用户睡觉时间（指几点上床睡觉，不是时长）：
{state.get("sleep_time")}{extra}

请输出：
1. 明天时间安排
2. 是否需要调整作息
"""

        analysis = ask_llm(system_prompt, user_prompt)

        return AgentResult(
            message=analysis,
            state_update={
                "calendar_analysis": analysis,
                "calendar_analysis_done": True,
            },
        )