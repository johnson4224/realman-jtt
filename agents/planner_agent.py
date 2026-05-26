from agents.calendar_agent import calendar_agent
from agents.weather_agent import weather_agent
from agents.food_agent import food_agent
from agents.transport_agent import transport_agent

def planner_agent(user_state):

    result = {}

    print("===== Planner Agent 启动 =====")

    # 1. Calendar
    print("-> Handoff 给 Calendar Agent")
    result["calendar"] = calendar_agent(user_state)

    # 2. Weather
    print("-> Handoff 给 Weather Agent")
    weather_result = weather_agent(user_state)

    result["weather"] = weather_result

    # 3. 根据天气决定是否继续handoff
    if "雨" in weather_result:

        print("-> 检测到下雨")
        print("-> Handoff 给 Transport Agent")

        result["transport"] = transport_agent(user_state)

    # 4. Food
    print("-> Handoff 给 Food Agent")
    result["food"] = food_agent(user_state)

    return result