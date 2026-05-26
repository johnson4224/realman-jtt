from core.agent import Agent, AgentResult, AcceptRule, RejectRule, HandoffRule
from core.memory import SharedMemory
from core.ask import ask
from tools.llm import ask_llm


class FoodAgent(Agent):
    def __init__(self):
        super().__init__(
            name="FoodAgent",
            description="饮食健康助手：根据库存和健康目标推荐饮食",
        )

    def _setup_rules(self):
        self.accept_rules = [
            AcceptRule(
                name="has_inventory_and_goal",
                description="state中存在inventory和health_goal时接收任务",
                condition=lambda agent, state: (
                    state.has("inventory") and state.has("health_goal")
                ),
            ),
        ]

        self.reject_rules = [
            RejectRule(
                name="already_planned",
                description="如果已经规划过饮食则拒绝",
                condition=lambda agent, state: state.has("food_done"),
            ),
        ]

        self.handoff_rules = [
            HandoffRule(
                name="handoff_to_health",
                description="饮食规划完成后，如果睡眠不好则handoff给HealthAgent",
                condition=lambda agent, state: (
                    state.has("sleep_time")
                    and "凌晨" in str(state.get("sleep_time", ""))
                ),
                target=lambda agent, state: "HealthAgent",
            ),
            HandoffRule(
                name="end_workflow",
                description="饮食规划完成，睡眠正常，流程结束",
                condition=lambda agent, state: True,
                target=lambda agent, state: None,
            ),
        ]

    def clarify(self, state: SharedMemory):
        inventory = state.get("inventory", "")
        if "食堂" in state.get("go_out", "") and not state.has("meal_budget"):
            budget = ask(f"\n[{self.name}] 去食堂吃的话，早餐午餐晚餐分别大概多少预算？或者随便说个总预算 ").strip()
            state.set("meal_budget", budget)
        if not state.has("food_preference"):
            preference = ask(f"[{self.name}] 有什么特别爱吃或不爱吃的吗？（没有就回车跳过） ").strip()
            if preference:
                state.set("food_preference", preference)

    def execute(self, state: SharedMemory) -> AgentResult:
        system_prompt = """
你是饮食健康助手。
负责：
- 根据库存推荐饮食
- 根据健康目标安排饮食
规则：
- 只根据用户已提供的信息做规划
- 不要反问用户问题，信息不够就按已知的最佳推测处理
- 直接输出推荐方案，不要提问
"""

        extra = ""
        if state.has("meal_budget"):
            extra += f"\n用餐预算：{state.get('meal_budget')}"
        if state.has("food_preference"):
            extra += f"\n饮食偏好：{state.get('food_preference')}"
        if state.has("user_feedback"):
            extra += f"\n用户反馈（请根据此反馈调整方案）：{state.get('user_feedback')}"

        user_prompt = f"""
用户目标：
{state.get("health_goal")}

库存：
{state.get("inventory")}{extra}

请推荐：
1. 早餐
2. 午餐
3. 晚餐
"""

        meal_plan = ask_llm(system_prompt, user_prompt)

        return AgentResult(
            message=meal_plan,
            state_update={
                "meal_plan": meal_plan,
                "food_done": True,
            },
        )