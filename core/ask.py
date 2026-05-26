"""
可切换的 ask 函数。CLI 下用 input()，Kivy GUI 下可替换成弹窗。
"""

_ask_func = None


def set_ask_func(func):
    global _ask_func
    _ask_func = func


def ask(question: str) -> str:
    if _ask_func:
        return _ask_func(question)
    return input(question)
