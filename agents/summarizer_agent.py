from tools.llm import ask_llm


def summarize(results: list[dict], user_input: dict) -> str:
    """把所有Agent的输出汇总成一段总结"""

    parts = []
    for r in results:
        parts.append(f"## {r['agent']}\n{r['message']}")

    agent_outputs = "\n\n".join(parts)

    user_info = "\n".join([f"- {k}: {v}" for k, v in user_input.items()])

    system_prompt = """
你是家庭秘书的总结助手。
负责：把多个专业Agent的分析结果整合成一份简洁、清晰的明日规划建议。
要求：
- 按时间线组织（早上→中午→下午→晚上）
- 去掉重复内容
- 去掉推理过程，只保留结论和建议
- 用自然语言，像朋友在跟你说话
- 末尾加一条"一句话提醒"
- 确保最终建议符合用户的实际条件和原始输入
"""

    user_prompt = f"""
## 用户原始输入
{user_info}

## 各Agent输出的原始结果
{agent_outputs}

请基于用户的原始输入，整合各Agent的分析结果，输出一份明日规划建议。
"""

    summary = ask_llm(system_prompt, user_prompt)
    return summary