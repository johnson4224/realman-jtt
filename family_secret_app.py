"""
家庭秘书 - Kivy 图形界面版
"""

import sys
import os
import threading
import queue

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kivy.config import Config
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "700")

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.text import LabelBase

# 跨平台中文字体加载
_FONT_CANDIDATES = [
    os.path.join(os.path.dirname(__file__), "font.ttf"),       # APK 内置
    "C:/Windows/Fonts/msyh.ttc",                                # Windows 开发
]
_cn_font = None
for _fp in _FONT_CANDIDATES:
    if os.path.exists(_fp):
        _cn_font = _fp
        break
if _cn_font:
    LabelBase.register(name="CN", fn_regular=_cn_font)


class CNLabel(Label):
    font_name = "CN"


class CNButton(Button):
    font_name = "CN"


class CNLabel(Label):
    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", "CN")
        super().__init__(**kwargs)


class CNButton(Button):
    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", "CN")
        super().__init__(**kwargs)


class CNTextInput(TextInput):
    def __init__(self, **kwargs):
        kwargs.setdefault("font_name", "CN")
        super().__init__(**kwargs)


from core.memory import SharedMemory
from core.router import AgentRouter, EventLoop
from core.ask import set_ask_func
from agents.calendar_agent import CalendarAgent
from agents.weather_agent import WeatherAgent
from agents.food_agent import FoodAgent
from agents.transport_agent import TransportAgent
from agents.health_agent import HealthAgent
from agents.summarizer_agent import summarize


class FamilySecretApp(App):
    def build(self):
        self.title = "家庭秘书"
        self.state = None
        self.router = None
        self.question_queue = queue.Queue()
        self.answer_queue = queue.Queue()
        self.chain_done = threading.Event()
        self.chain_summary = ""
        self.chain_trace = ""
        self.chain_error = None

        root = BoxLayout(orientation="vertical", padding=15, spacing=8)

        root.add_widget(CNLabel(
            text="家庭秘书", size_hint_y=None, height=50,
            font_size=26, bold=True,
        ))

        scroll = ScrollView(size_hint=(1, 1))
        self.content = BoxLayout(orientation="vertical", size_hint_y=None, spacing=10)
        self.content.bind(minimum_height=self.content.setter("height"))
        scroll.add_widget(self.content)
        root.add_widget(scroll)

        self._build_form()
        return root

    def _build_form(self, feedback_text=""):
        self.content.clear_widgets()

        form = GridLayout(cols=2, size_hint_y=None, height=350, spacing=8)
        form.add_widget(CNLabel(text="城市", halign="right"))
        self.input_city = CNTextInput(multiline=False, text="合肥")
        form.add_widget(self.input_city)

        form.add_widget(CNLabel(text="明天固定安排", halign="right"))
        self.input_calendar = CNTextInput(multiline=False)
        form.add_widget(self.input_calendar)

        form.add_widget(CNLabel(text="明天出门吗", halign="right"))
        self.input_goout = CNTextInput(multiline=False)
        form.add_widget(self.input_goout)

        form.add_widget(CNLabel(text="健康目标", halign="right"))
        self.input_health = CNTextInput(multiline=False)
        form.add_widget(self.input_health)

        form.add_widget(CNLabel(text="冰箱食材", halign="right"))
        self.input_inventory = CNTextInput(multiline=False)
        form.add_widget(self.input_inventory)

        form.add_widget(CNLabel(text="今晚几点睡", halign="right"))
        self.input_sleep = CNTextInput(multiline=False)
        form.add_widget(self.input_sleep)

        self.content.add_widget(form)

        if feedback_text:
            self.content.add_widget(CNLabel(
                text=f"上一轮反馈：{feedback_text}",
                size_hint_y=None, height=30, color=(1, 0.6, 0, 1),
            ))

        btn = CNButton(
            text="开始规划", size_hint_y=None, height=50,
            background_color=(0.2, 0.6, 1, 1),
        )
        btn.bind(on_press=self._start_chain)
        self.content.add_widget(btn)

    def _collect_input(self):
        st = self.input_sleep.text.strip()
        if st.isdigit():
            st = f"凌晨{st}点" if int(st) <= 5 else f"{st}点"
        return {
            "city": self.input_city.text.strip(),
            "calendar": self.input_calendar.text.strip(),
            "go_out": self.input_goout.text.strip(),
            "health_goal": self.input_health.text.strip(),
            "inventory": self.input_inventory.text.strip(),
            "sleep_time": st,
        }

    def _gui_ask(self, question):
        self.question_queue.put(question)
        return self.answer_queue.get()

    def _start_chain(self, _btn=None):
        user_data = self._collect_input()
        self.state = SharedMemory(user_data)
        self.router = AgentRouter()
        self.router.register_many([
            CalendarAgent(), WeatherAgent(), TransportAgent(),
            FoodAgent(), HealthAgent(),
        ])

        self.content.clear_widgets()
        self.content.add_widget(CNLabel(
            text="正在规划中...", size_hint_y=None, height=50, font_size=18,
        ))

        self.question_queue = queue.Queue()
        self.answer_queue = queue.Queue()
        self.chain_done.clear()
        self.chain_error = None

        set_ask_func(self._gui_ask)

        def _run():
            try:
                while True:
                    el = EventLoop(self.router, self.state, max_steps=20)
                    results = el.run()
                    trace = " -> ".join(self.state.agent_trace)
                    summary = summarize(results, self.state.state)
                    self.chain_summary = summary
                    self.chain_trace = trace
                    self.chain_done.set()

                    feedback_ev = threading.Event()
                    self._feedback_event = feedback_ev
                    self._feedback_result = None
                    feedback_ev.wait()
                    fb = self._feedback_result
                    if not fb:
                        return
                    for k in list(self.state.state.keys()):
                        if k.endswith("_done"):
                            del self.state.state[k]
                    self.state.set("user_feedback", fb)
            except Exception as e:
                self.chain_error = e
                self.chain_done.set()

        t = threading.Thread(target=_run, daemon=True)
        t.start()
        Clock.schedule_interval(self._check_progress, 0.2)

    def _check_progress(self, _dt):
        try:
            q = self.question_queue.get_nowait()
            Clock.schedule_once(lambda dt: self._show_question_dialog(q))
        except queue.Empty:
            pass

        if self.chain_done.is_set():
            Clock.unschedule(self._check_progress)
            if self.chain_error:
                self._show_error(str(self.chain_error))
            else:
                self._show_result()

    def _show_question_dialog(self, question):
        content = BoxLayout(orientation="vertical", spacing=10, padding=10)
        content.add_widget(CNLabel(
            text=question, size_hint_y=None, height=50,
            text_size=(300, None), halign="left",
        ))
        ti = CNTextInput(multiline=False, size_hint_y=None, height=40)
        content.add_widget(ti)

        def on_answer(_btn):
            self.answer_queue.put(ti.text.strip())
            popup.dismiss()

        btn = CNButton(
            text="确定", size_hint_y=None, height=40,
            background_color=(0.2, 0.6, 1, 1),
        )
        btn.bind(on_press=on_answer)
        content.add_widget(btn)

        popup = Popup(
            title="追问", title_font="CN",
            content=content, size_hint=(0.85, 0.4), auto_dismiss=False,
        )
        popup.open()

    def _show_result(self):
        self.content.clear_widgets()

        self.content.add_widget(CNLabel(
            text=f"执行路径: {self.chain_trace}",
            size_hint_y=None, height=30,
            color=(0.4, 0.8, 1, 1), font_size=14,
        ))

        sv = ScrollView(size_hint_y=None, height=350)
        summary_label = CNLabel(
            text=self.chain_summary,
            size_hint_y=None,
            text_size=(360, None),
            halign="left", valign="top",
            font_size=15,
        )
        summary_label.bind(
            texture_size=lambda obj, val: setattr(obj, "height", val[1])
        )
        sv.add_widget(summary_label)
        self.content.add_widget(sv)

        box = BoxLayout(size_hint_y=None, height=50, spacing=10)
        fb_btn = CNButton(
            text="不满意，要修改", background_color=(1, 0.5, 0, 1),
        )
        fb_btn.bind(on_press=lambda x: self._show_feedback_input())
        box.add_widget(fb_btn)
        ok_btn = CNButton(
            text="满意，结束", background_color=(0.2, 0.8, 0.2, 1),
        )
        ok_btn.bind(on_press=lambda x: App.get_running_app().stop())
        box.add_widget(ok_btn)
        self.content.add_widget(box)

    def _show_feedback_input(self):
        self.content.clear_widgets()
        self.content.add_widget(CNLabel(
            text="想改什么？", size_hint_y=None, height=30, font_size=16,
        ))
        ti = CNTextInput(multiline=True, size_hint_y=None, height=120)
        self.content.add_widget(ti)

        def on_submit(_btn):
            fb = ti.text.strip()
            if fb:
                self._feedback_result = fb
                self._feedback_event.set()
                Clock.schedule_once(lambda dt: self._show_rerun_status())
            else:
                self.content.add_widget(CNLabel(
                    text="请输入要修改的内容", size_hint_y=None, height=30,
                    color=(1, 0, 0, 1),
                ))

        btn = CNButton(
            text="重新规划", size_hint_y=None, height=45,
            background_color=(0.2, 0.6, 1, 1),
        )
        btn.bind(on_press=on_submit)
        self.content.add_widget(btn)

    def _show_rerun_status(self):
        self.content.clear_widgets()
        self.content.add_widget(CNLabel(
            text="正在重新规划...", size_hint_y=None, height=50, font_size=18,
        ))

        self.question_queue = queue.Queue()
        self.answer_queue = queue.Queue()
        self.chain_done.clear()
        self.chain_error = None

        t = threading.Thread(target=self._rerun, daemon=True)
        t.start()
        Clock.schedule_interval(self._check_progress, 0.2)

    def _rerun(self):
        try:
            el = EventLoop(self.router, self.state, max_steps=20)
            results = el.run()
            trace = " -> ".join(self.state.agent_trace)
            summary = summarize(results, self.state.state)
            self.chain_summary = summary
            self.chain_trace = trace
            self.chain_done.set()
        except Exception as e:
            self.chain_error = e
            self.chain_done.set()

    def _show_error(self, msg):
        self.content.clear_widgets()
        self.content.add_widget(CNLabel(
            text=f"出错了：{msg}", size_hint_y=None, height=50,
            color=(1, 0, 0, 1),
        ))
        btn = CNButton(text="返回重试", size_hint_y=None, height=50)
        btn.bind(on_press=lambda x: self._build_form())
        self.content.add_widget(btn)


if __name__ == "__main__":
    FamilySecretApp().run()
