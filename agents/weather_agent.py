from core.agent import Agent, AgentResult, AcceptRule, RejectRule, HandoffRule
from core.memory import SharedMemory
from tools.weather_tool import get_weather
from tools.llm import ask_llm


class WeatherAgent(Agent):
    def __init__(self):
        super().__init__(
            name="WeatherAgent",
            description="天气分析助手：获取天气数据，分析是否影响出行和交通",
        )

    def _setup_rules(self):
        self.accept_rules = [
            AcceptRule(
                name="has_city",
                description="state中存在city时接收任务",
                condition=lambda agent, state: state.has("city"),
            ),
        ]

        self.reject_rules = [
            RejectRule(
                name="already_checked",
                description="如果天气已经被检查过则拒绝",
                condition=lambda agent, state: state.has("weather_checked"),
            ),
        ]

        self.handoff_rules = [
            HandoffRule(
                name="rain_triggers_transport",
                description="检测到下雨时，自主handoff给TransportAgent",
                condition=lambda agent, state: (
                    state.has("weather_contains_rain")
                    and state.get("weather_contains_rain") is True
                ),
                target=lambda agent, state: "TransportAgent",
            ),
            HandoffRule(
                name="no_rain_skip_transport",
                description="没有下雨时，跳过TransportAgent，handoff给FoodAgent",
                condition=lambda agent, state: (
                    not state.get("weather_contains_rain", False)
                ),
                target=lambda agent, state: "FoodAgent",
            ),
        ]

    def execute(self, state: SharedMemory) -> AgentResult:
        city = state.get("city")
        weather = get_weather(city)

        system_prompt = """
你是天气分析助手。
负责：
- 分析天气
- 判断是否影响出行
"""

        user_prompt = f"""
天气数据：
{weather}

请分析：
1. 是否适合出门
2. 是否影响交通
"""

        if state.has("user_feedback"):
            user_prompt += f"\n用户反馈（请参考）：{state.get('user_feedback')}\n"

        analysis = ask_llm(system_prompt, user_prompt)

        weather_str = str(weather).lower()
        contains_rain = any(kw in weather_str for kw in ["雨", "rain", "小雨", "中雨", "大雨", "暴雨"])

        return AgentResult(
            message=analysis,
            state_update={
                "weather_data": weather,
                "weather_analysis": analysis,
                "weather_checked": True,
                "weather_contains_rain": contains_rain,
            },
        )