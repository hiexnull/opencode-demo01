import os
import sys
import json
import threading
import math
from datetime import datetime, timedelta

os.environ["KIVY_NO_CONSOLELOG"] = "1"

from kivy.config import Config
Config.set("kivy", "exit_on_escape", "0")
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "700")

from kivy.app import App
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.progressbar import ProgressBar
from kivy.uix.image import Image
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.properties import (
    NumericProperty, StringProperty, BooleanProperty,
    ListProperty, ObjectProperty, ColorProperty
)

import database as db

db.init_db()


THEME = {
    "bg": "#1A1A2E",
    "surface": "#16213E",
    "card": "#0F3460",
    "primary": "#E94560",
    "accent": "#FFD700",
    "text": "#EEEEEE",
    "text_secondary": "#AAAAAA",
    "success": "#4CAF50",
    "warning": "#FFC107",
    "danger": "#F44336",
}


class RoundedButton(Button):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*get_color_from_hex(self.theme_color if hasattr(self, 'theme_color') else THEME["primary"]))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[12])


class RoundedInput(TextInput):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = (0, 0, 0, 0)
        self.background_normal = ""
        self.hint_text_color = get_color_from_hex(THEME["text_secondary"])
        self.foreground_color = get_color_from_hex(THEME["text"])
        self.cursor_color = get_color_from_hex(THEME["accent"])
        self.padding = [15, 12]
        self.font_size = 16
        self.bind(pos=self.update_canvas, size=self.update_canvas)

    def update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(0.1, 0.15, 0.25, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])
            Color(0.3, 0.4, 0.6, 0.3)
            Line(rounded_rectangle=self.pos + self.size + [10], width=1.5)


class StudyApp(App):
    def build(self):
        self.title = "StudyMate - 学习助手"
        Window.clearcolor = get_color_from_hex(THEME["bg"])
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(PomodoroScreen(name="pomodoro"))
        sm.add_widget(TodoScreen(name="todo"))
        sm.add_widget(EbookScreen(name="ebook"))
        sm.add_widget(TagScreen(name="tags"))
        sm.add_widget(GoalScreen(name="goals"))
        sm.add_widget(StatsScreen(name="stats"))
        return sm

    def show_popup(self, title, content, btn_text="确定"):
        layout = BoxLayout(orientation="vertical", spacing=15, padding=20)
        layout.add_widget(Label(text=content, color=get_color_from_hex(THEME["text"]), font_size=15, halign="center"))
        btn = Button(text=btn_text, size_hint_y=0.35, background_normal="",
                      background_color=get_color_from_hex(THEME["primary"]), color=(1,1,1,1))
        layout.add_widget(btn)
        popup = Popup(title=title, content=layout, size_hint=(0.8, 0.4),
                       background_color=get_color_from_hex(THEME["surface"]),
                       separator_color=get_color_from_hex(THEME["primary"]),
                       title_color=get_color_from_hex(THEME["accent"]))
        btn.bind(on_release=popup.dismiss)
        popup.open()


class MainScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def on_enter(self):
        self.refresh()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=15)
        with layout.canvas.before:
            Color(*get_color_from_hex(THEME["bg"]))
            Rectangle(pos=layout.pos, size=layout.size)

        header = BoxLayout(orientation="horizontal", size_hint_y=0.1)
        title = Label(text="StudyMate", font_size=28, bold=True,
                       color=get_color_from_hex(THEME["accent"]), halign="left")
        header.add_widget(title)
        self.xp_label = Label(text="0 XP", font_size=16, color=get_color_from_hex(THEME["text_secondary"]),
                               size_hint_x=0.4, halign="right")
        header.add_widget(self.xp_label)
        layout.add_widget(header)

        self.streak_label = Label(text="连续学习: 0 天", font_size=14,
                                   color=get_color_from_hex(THEME["text_secondary"]), size_hint_y=0.05)
        layout.add_widget(self.streak_label)

        btn_style = {"size_hint_y": None, "height": 60, "font_size": 18,
                      "background_normal": "", "color": (1,1,1,1)}

        items = [
            ("🍅  番茄钟", "pomodoro", THEME["primary"]),
            ("📋  待办清单", "todo", "#E67E22"),
            ("📚  电子书搜索", "ebook", "#2ECC71"),
            ("🏷️  标签管理", "tags", "#9B59B6"),
            ("🎯  学习目标", "goals", "#1ABC9C"),
            ("📊  统计成就", "stats", "#3498DB"),
        ]

        scroll = ScrollView()
        grid = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[0,5,0,5])
        grid.bind(minimum_height=grid.setter("height"))

        for text, screen, color in items:
            btn = Button(text=text, **btn_style)
            btn.background_color = get_color_from_hex(color)
            btn.bind(on_release=lambda btn, s=screen: self.goto(s))
            grid.add_widget(btn)

        scroll.add_widget(grid)
        layout.add_widget(scroll)
        self.add_widget(layout)

    def refresh(self):
        total_xp = db.get_total_xp()
        self.xp_label.text = f"{total_xp} XP"
        streak = self.calc_streak()
        self.streak_label.text = f"连续学习: {streak} 天"

    def calc_streak(self):
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT DISTINCT date(created_at) d FROM xp_log ORDER BY d DESC")
        days = [row['d'] for row in c.fetchall()]
        conn.close()
        if not days:
            return 0
        streak = 1
        today = datetime.now().date()
        if days[0] != today.isoformat():
            if days[0] != (today - timedelta(1)).isoformat():
                return 0
        for i in range(1, len(days)):
            d1 = datetime.strptime(days[i-1], "%Y-%m-%d").date()
            d2 = datetime.strptime(days[i], "%Y-%m-%d").date()
            if (d1 - d2).days == 1:
                streak += 1
            else:
                break
        return streak

    def goto(self, screen):
        self.manager.current = screen


class PomodoroScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.work_min = int(db.get_setting("pomodoro_work", "25"))
        self.break_min = int(db.get_setting("pomodoro_break", "5"))
        self.remaining = self.work_min * 60
        self.is_running = False
        self.is_break = False
        self.session_id = None
        self.timer_event = None
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=15, padding=20)
        with layout.canvas.before:
            Color(*get_color_from_hex(THEME["bg"]))
            Rectangle(pos=layout.pos, size=layout.size)

        top = BoxLayout(orientation="horizontal", size_hint_y=0.08)
        back = Button(text="← 返回", font_size=16, background_normal="",
                       color=get_color_from_hex(THEME["text"]), size_hint_x=0.3)
        back.bind(on_release=lambda x: self.stop_timer() or setattr(self.manager, "current", "main"))
        top.add_widget(back)
        top.add_widget(Label(text="🍅 番茄钟", font_size=22, bold=True, color=get_color_from_hex(THEME["accent"])))
        top.add_widget(Label(size_hint_x=0.3))
        layout.add_widget(top)

        self.status_label = Label(text="专注时间", font_size=18, color=get_color_from_hex(THEME["text"]), size_hint_y=0.06)
        layout.add_widget(self.status_label)

        self.timer_label = Label(text=self.format_time(self.remaining), font_size=72, bold=True,
                                  color=get_color_from_hex(THEME["primary"]), size_hint_y=0.3)
        layout.add_widget(self.timer_label)

        circle_box = BoxLayout(orientation="horizontal", size_hint_y=0.1)
        self.progress = ProgressBar(max=1, value=1, size_hint=(0.8, 0.4))
        self.progress.color = get_color_from_hex(THEME["primary"])
        circle_box.add_widget(self.progress)
        layout.add_widget(circle_box)

        btn_box = BoxLayout(orientation="horizontal", spacing=20, size_hint_y=0.12)
        self.start_btn = Button(text="▶ 开始", font_size=20, background_normal="",
                                 background_color=get_color_from_hex(THEME["success"]), color=(1,1,1,1))
        self.start_btn.bind(on_release=self.toggle_timer)
        btn_box.add_widget(self.start_btn)

        self.reset_btn = Button(text="↺ 重置", font_size=20, background_normal="",
                                 background_color=get_color_from_hex(THEME["danger"]), color=(1,1,1,1))
        self.reset_btn.bind(on_release=self.reset_timer)
        btn_box.add_widget(self.reset_btn)
        layout.add_widget(btn_box)

        setting_box = BoxLayout(orientation="horizontal", spacing=10, size_hint_y=0.1)
        setting_box.add_widget(Label(text="专注:", font_size=14, color=get_color_from_hex(THEME["text"]), size_hint_x=0.2))
        self.work_input = RoundedInput(text=str(self.work_min), input_filter="int", size_hint_x=0.15, font_size=16)
        setting_box.add_widget(self.work_input)
        setting_box.add_widget(Label(text="分钟", font_size=14, color=get_color_from_hex(THEME["text"]), size_hint_x=0.2))
        setting_box.add_widget(Label(text="休息:", font_size=14, color=get_color_from_hex(THEME["text"]), size_hint_x=0.2))
        self.break_input = RoundedInput(text=str(self.break_min), input_filter="int", size_hint_x=0.15, font_size=16)
        setting_box.add_widget(self.break_input)
        setting_box.add_widget(Label(text="分钟", font_size=14, color=get_color_from_hex(THEME["text"]), size_hint_x=0.2))
        layout.add_widget(setting_box)

        apply_btn = Button(text="应用设置", font_size=14, size_hint_y=0.06, background_normal="",
                            background_color=get_color_from_hex(THEME["card"]), color=(1,1,1,1))
        apply_btn.bind(on_release=self.apply_settings)
        layout.add_widget(apply_btn)

        self.daily_count_label = Label(text="今日完成: 0 个番茄钟", font_size=14,
                                        color=get_color_from_hex(THEME["text_secondary"]), size_hint_y=0.06)
        layout.add_widget(self.daily_count_label)

        self.add_widget(layout)

    def format_time(self, seconds):
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def toggle_timer(self, btn):
        if not self.is_running:
            if not self.session_id:
                conn = db.get_conn()
                c = conn.cursor()
                c.execute("INSERT INTO pomodoro_sessions (duration_minutes, break_minutes) VALUES (?,?)",
                          (self.work_min, self.break_min))
                conn.commit()
                self.session_id = c.lastrowid
                conn.close()
            self.is_running = True
            self.timer_event = Clock.schedule_interval(self.tick, 1)
            self.start_btn.text = "⏸ 暂停"
            self.start_btn.background_color = get_color_from_hex(THEME["warning"])
        else:
            self.is_running = False
            if self.timer_event:
                self.timer_event.cancel()
            self.start_btn.text = "▶ 继续"
            self.start_btn.background_color = get_color_from_hex(THEME["success"])

    def tick(self, dt):
        self.remaining -= 1
        self.timer_label.text = self.format_time(self.remaining)
        total = (self.break_min * 60) if self.is_break else (self.work_min * 60)
        self.progress.value = self.remaining / total

        if self.remaining <= 0:
            self.timer_complete()

    def timer_complete(self):
        if self.timer_event:
            self.timer_event.cancel()
        self.is_running = False

        if not self.is_break:
            conn = db.get_conn()
            c = conn.cursor()
            c.execute("UPDATE pomodoro_sessions SET completed=1, ended_at=datetime('now','localtime') WHERE id=?",
                      (self.session_id,))
            conn.commit()
            conn.close()
            db.add_xp("pomodoro", self.session_id, 10)
            self.session_id = None

            App.get_running_app().show_popup("🎉 太棒了！", f"完成了一个番茄钟！获得 10 XP")
            self.is_break = True
            self.remaining = self.break_min * 60
            self.status_label.text = "☕ 休息时间"
            self.status_label.color = get_color_from_hex(THEME["success"])
            self.timer_label.color = get_color_from_hex(THEME["success"])
        else:
            self.is_break = False
            self.remaining = self.work_min * 60
            self.status_label.text = "专注时间"
            self.status_label.color = get_color_from_hex(THEME["text"])
            self.timer_label.color = get_color_from_hex(THEME["primary"])
            App.get_running_app().show_popup("⏰ 休息结束", "开始新的专注周期吧！")

        self.progress.value = 1
        self.timer_label.text = self.format_time(self.remaining)
        self.start_btn.text = "▶ 开始"
        self.start_btn.background_color = get_color_from_hex(THEME["success"])
        self.update_daily_count()

    def reset_timer(self, btn=None):
        self.stop_timer()
        self.is_break = False
        self.remaining = self.work_min * 60
        self.session_id = None
        self.timer_label.text = self.format_time(self.remaining)
        self.progress.value = 1
        self.status_label.text = "专注时间"
        self.status_label.color = get_color_from_hex(THEME["text"])
        self.timer_label.color = get_color_from_hex(THEME["primary"])
        self.start_btn.text = "▶ 开始"
        self.start_btn.background_color = get_color_from_hex(THEME["success"])

    def stop_timer(self):
        self.is_running = False
        if self.timer_event:
            self.timer_event.cancel()
            self.timer_event = None

    def apply_settings(self, btn=None):
        try:
            w = int(self.work_input.text)
            b = int(self.break_input.text)
            if w < 1 or b < 1:
                raise ValueError
            self.work_min = w
            self.break_min = b
            db.set_setting("pomodoro_work", str(w))
            db.set_setting("pomodoro_break", str(b))
            self.reset_timer()
            App.get_running_app().show_popup("设置已保存", f"专注 {w} 分钟 / 休息 {b} 分钟")
        except:
            App.get_running_app().show_popup("错误", "请输入有效数字")

    def update_daily_count(self):
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM pomodoro_sessions WHERE completed=1 AND date(ended_at)=date('now','localtime')")
        count = c.fetchone()[0]
        conn.close()
        self.daily_count_label.text = f"今日完成: {count} 个番茄钟"

    def on_enter(self):
        self.update_daily_count()


class TodoScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=15)
        with layout.canvas.before:
            Color(*get_color_from_hex(THEME["bg"]))
            Rectangle(pos=layout.pos, size=layout.size)

        top = BoxLayout(orientation="horizontal", size_hint_y=0.08)
        back = Button(text="← 返回", font_size=16, background_normal="",
                       color=get_color_from_hex(THEME["text"]), size_hint_x=0.25)
        back.bind(on_release=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        top.add_widget(Label(text="📋 待办清单", font_size=22, bold=True, color=get_color_from_hex(THEME["accent"])))
        top.add_widget(Label(size_hint_x=0.25))
        layout.add_widget(top)

        input_box = BoxLayout(orientation="horizontal", size_hint_y=0.08, spacing=8)
        self.task_input = RoundedInput(hint_text="输入新任务...", size_hint_x=0.7, font_size=15)
        input_box.add_widget(self.task_input)
        add_btn = Button(text="添加", font_size=16, background_normal="",
                          background_color=get_color_from_hex(THEME["success"]), color=(1,1,1,1), size_hint_x=0.3)
        add_btn.bind(on_release=self.add_task)
        input_box.add_widget(add_btn)
        layout.add_widget(input_box)

        filter_box = BoxLayout(orientation="horizontal", size_hint_y=0.06, spacing=5)
        self.filter_all = Button(text="全部", font_size=13, background_normal="",
                                  background_color=get_color_from_hex(THEME["primary"]), color=(1,1,1,1))
        self.filter_pending = Button(text="待办", font_size=13, background_normal="",
                                      background_color=get_color_from_hex(THEME["card"]), color=(1,1,1,1))
        self.filter_done = Button(text="已完成", font_size=13, background_normal="",
                                   background_color=get_color_from_hex(THEME["card"]), color=(1,1,1,1))
        self.filter_all.bind(on_release=lambda x: self.load_tasks("all"))
        self.filter_pending.bind(on_release=lambda x: self.load_tasks("pending"))
        self.filter_done.bind(on_release=lambda x: self.load_tasks("done"))
        filter_box.add_widget(self.filter_all)
        filter_box.add_widget(self.filter_pending)
        filter_box.add_widget(self.filter_done)
        layout.add_widget(filter_box)

        self.scroll = ScrollView()
        self.task_list = GridLayout(cols=1, spacing=6, size_hint_y=None, padding=[0,5,0,5])
        self.task_list.bind(minimum_height=self.task_list.setter("height"))
        self.scroll.add_widget(self.task_list)
        layout.add_widget(self.scroll)

        self.current_filter = "all"
        self.add_widget(layout)

    def add_task(self, btn=None):
        title = self.task_input.text.strip()
        if not title:
            return
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
        conn.commit()
        conn.close()
        self.task_input.text = ""
        self.load_tasks(self.current_filter)

    def load_tasks(self, filter_type="all"):
        self.current_filter = filter_type
        self.task_list.clear_widgets()
        for b in [self.filter_all, self.filter_pending, self.filter_done]:
            b.background_color = get_color_from_hex(THEME["card"])
        {
            "all": self.filter_all,
            "pending": self.filter_pending,
            "done": self.filter_done,
        }[filter_type].background_color = get_color_from_hex(THEME["primary"])

        conn = db.get_conn()
        c = conn.cursor()
        if filter_type == "all":
            c.execute("SELECT * FROM tasks ORDER BY status='pending' DESC, created_at DESC")
        else:
            c.execute("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC", (filter_type,))
        tasks = c.fetchall()
        conn.close()

        if not tasks:
            self.task_list.add_widget(Label(text="暂无任务，添加一个吧 📝", color=get_color_from_hex(THEME["text_secondary"]),
                                             font_size=15, size_hint_y=None, height=60))
            return

        for t in tasks:
            self.task_list.add_widget(TaskCard(t))

    def on_enter(self):
        self.load_tasks()


class TaskCard(BoxLayout):
    def __init__(self, task, **kwargs):
        super().__init__(**kwargs)
        self.task_id = task['id']
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = 60
        self.spacing = 8
        self.padding = [10, 5]

        with self.canvas.before:
            Color(*get_color_from_hex(THEME["surface"]))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[8])

        is_done = task['status'] == 'done'
        done_btn = Button(text="✅" if is_done else "⬜", font_size=18,
                           size_hint_x=0.12, background_normal="", color=(1,1,1,1))
        done_btn.bind(on_release=self.toggle_done)
        self.add_widget(done_btn)

        title = task['title']
        if len(title) > 30:
            title = title[:30] + "..."
        lbl = Label(text=title, font_size=15, color=get_color_from_hex(THEME["text"]),
                     halign="left", valign="middle", size_hint_x=0.6)
        lbl.bind(size=lbl.setter("text_size"))
        if is_done:
            lbl.color = get_color_from_hex(THEME["text_secondary"])
        self.add_widget(lbl)

        del_btn = Button(text="✕", font_size=16, size_hint_x=0.12,
                          background_normal="", color=get_color_from_hex(THEME["danger"]))
        del_btn.bind(on_release=self.delete_task)
        self.add_widget(del_btn)

    def toggle_done(self, btn):
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT status FROM tasks WHERE id=?", (self.task_id,))
        row = c.fetchone()
        if row['status'] == 'done':
            c.execute("UPDATE tasks SET status='pending', completed_at=NULL WHERE id=?", (self.task_id,))
        else:
            c.execute("UPDATE tasks SET status='done', completed_at=datetime('now','localtime') WHERE id=?",
                      (self.task_id,))
            db.add_xp("task", self.task_id, 5)
        conn.commit()
        conn.close()
        App.get_running_app().root.get_screen("todo").load_tasks(
            App.get_running_app().root.get_screen("todo").current_filter
        )

    def delete_task(self, btn):
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("DELETE FROM tasks WHERE id=?", (self.task_id,))
        conn.commit()
        conn.close()
        App.get_running_app().root.get_screen("todo").load_tasks(
            App.get_running_app().root.get_screen("todo").current_filter
        )


class EbookScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=15)
        with layout.canvas.before:
            Color(*get_color_from_hex(THEME["bg"]))
            Rectangle(pos=layout.pos, size=layout.size)

        top = BoxLayout(orientation="horizontal", size_hint_y=0.08)
        back = Button(text="← 返回", font_size=16, background_normal="",
                       color=get_color_from_hex(THEME["text"]), size_hint_x=0.25)
        back.bind(on_release=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        top.add_widget(Label(text="📚 电子书搜索", font_size=22, bold=True, color=get_color_from_hex(THEME["accent"])))
        top.add_widget(Label(size_hint_x=0.25))
        layout.add_widget(top)

        search_box = BoxLayout(orientation="horizontal", size_hint_y=0.08, spacing=8)
        self.search_input = RoundedInput(hint_text="搜索关键词...", size_hint_x=0.7, font_size=15)
        search_box.add_widget(self.search_input)
        search_btn = Button(text="🔍 搜索", font_size=15, background_normal="",
                             background_color=get_color_from_hex(THEME["primary"]), color=(1,1,1,1), size_hint_x=0.3)
        search_btn.bind(on_release=self.do_search)
        search_box.add_widget(search_btn)
        layout.add_widget(search_box)

        self.scroll = ScrollView()
        self.result_list = GridLayout(cols=1, spacing=6, size_hint_y=None, padding=[0,5,0,5])
        self.result_list.bind(minimum_height=self.result_list.setter("height"))
        self.scroll.add_widget(self.result_list)
        layout.add_widget(self.scroll)
        self.add_widget(layout)

    def do_search(self, btn=None):
        keyword = self.search_input.text.strip().lower()
        self.result_list.clear_widgets()
        if not keyword:
            self.result_list.add_widget(Label(text="请输入搜索关键词", color=get_color_from_hex(THEME["text_secondary"]),
                                               font_size=15, size_hint_y=None, height=60))
            return

        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM books WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?",
                  (f"%{keyword}%", f"%{keyword}%"))
        books = c.fetchall()

        found = False
        for book in books:
            found = True
            card = BoxLayout(orientation="vertical", size_hint_y=None, height=80, padding=[10,5])
            with card.canvas.before:
                Color(*get_color_from_hex(THEME["surface"]))
                RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
            card.add_widget(Label(text=f"📖 {book['title']}", font_size=16, color=get_color_from_hex(THEME["accent"]),
                                   halign="left", size_hint_y=0.5))
            author = book['author'] or "未知作者"
            path = book['file_path'].split("\\")[-1].split("/")[-1]
            card.add_widget(Label(text=f"作者: {author}  |  文件: {path}", font_size=12,
                                   color=get_color_from_hex(THEME["text_secondary"]), halign="left", size_hint_y=0.4))
            self.result_list.add_widget(card)

        self.result_list.add_widget(Label(text="", size_hint_y=None, height=10))

        c.execute("""
            SELECT DISTINCT t.name FROM tags t
            JOIN book_tags bt ON t.id = bt.tag_id
            WHERE bt.book_id IN (SELECT id FROM books WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?)
        """, (f"%{keyword}%", f"%{keyword}%"))
        tags = [row['name'] for row in c.fetchall()]
        if tags:
            tag_lbl = Label(text=f"相关标签: {' '.join(tags)}", font_size=13,
                             color=get_color_from_hex(THEME["text_secondary"]), size_hint_y=None, height=30)
            self.result_list.add_widget(tag_lbl)
        conn.close()

        if not found:
            self.result_list.add_widget(Label(text="未找到匹配的电子书", color=get_color_from_hex(THEME["text_secondary"]),
                                               font_size=15, size_hint_y=None, height=60))

    def show_full_search(self, book_id):
        App.get_running_app().show_popup("全文搜索", "正在开发全文搜索功能...\n目前支持按书名和作者搜索")


class TagScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=15)
        with layout.canvas.before:
            Color(*get_color_from_hex(THEME["bg"]))
            Rectangle(pos=layout.pos, size=layout.size)

        top = BoxLayout(orientation="horizontal", size_hint_y=0.08)
        back = Button(text="← 返回", font_size=16, background_normal="",
                       color=get_color_from_hex(THEME["text"]), size_hint_x=0.25)
        back.bind(on_release=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        top.add_widget(Label(text="🏷️ 标签管理", font_size=22, bold=True, color=get_color_from_hex(THEME["accent"])))
        top.add_widget(Label(size_hint_x=0.25))
        layout.add_widget(top)

        input_box = BoxLayout(orientation="horizontal", size_hint_y=0.08, spacing=8)
        self.tag_input = RoundedInput(hint_text="输入标签名称...", size_hint_x=0.6, font_size=15)
        input_box.add_widget(self.tag_input)
        add_btn = Button(text="添加", font_size=16, background_normal="",
                          background_color=get_color_from_hex(THEME["success"]), color=(1,1,1,1), size_hint_x=0.2)
        add_btn.bind(on_release=self.add_tag)
        input_box.add_widget(add_btn)
        layout.add_widget(input_box)

        self.scroll = ScrollView()
        self.tag_list = GridLayout(cols=2, spacing=8, size_hint_y=None, padding=[0,5,0,5])
        self.tag_list.bind(minimum_height=self.tag_list.setter("height"))
        self.scroll.add_widget(self.tag_list)
        layout.add_widget(self.scroll)
        self.add_widget(layout)

    def add_tag(self, btn=None):
        name = self.tag_input.text.strip()
        if not name:
            return
        conn = db.get_conn()
        c = conn.cursor()
        try:
            c.execute("INSERT INTO tags (name) VALUES (?)", (name,))
            conn.commit()
            App.get_running_app().show_popup("成功", f"标签 '{name}' 已添加")
        except sqlite3.IntegrityError:
            App.get_running_app().show_popup("提示", "该标签已存在")
        conn.close()
        self.tag_input.text = ""
        self.load_tags()

    def load_tags(self):
        self.tag_list.clear_widgets()
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT t.*, (SELECT COUNT(*) FROM task_tags WHERE tag_id=t.id)+(SELECT COUNT(*) FROM book_tags WHERE tag_id=t.id) as cnt FROM tags t ORDER BY cnt DESC")
        tags = c.fetchall()
        conn.close()

        if not tags:
            self.tag_list.add_widget(Label(text="暂无标签", color=get_color_from_hex(THEME["text_secondary"]),
                                           font_size=15, size_hint_y=None, height=60))
            return

        for t in tags:
            card = BoxLayout(orientation="vertical", size_hint_y=None, height=70, padding=[8,5], spacing=3)
            with card.canvas.before:
                Color(*get_color_from_hex(THEME["surface"]))
                RoundedRectangle(pos=card.pos, size=card.size, radius=[8])
            name = t['name']
            if len(name) > 8:
                name = name[:8] + ".."
            card.add_widget(Label(text=f"#{name}", font_size=16, color=get_color_from_hex(THEME["accent"]),
                                   halign="center", size_hint_y=0.5))
            card.add_widget(Label(text=f"使用 {t['cnt']} 次", font_size=12,
                                   color=get_color_from_hex(THEME["text_secondary"]), halign="center", size_hint_y=0.3))
            self.tag_list.add_widget(card)

    def on_enter(self):
        self.load_tags()


class GoalScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        self.main_layout = BoxLayout(orientation="vertical", spacing=10, padding=15)
        with self.main_layout.canvas.before:
            Color(*get_color_from_hex(THEME["bg"]))
            Rectangle(pos=self.main_layout.pos, size=self.main_layout.size)
        self.build_content()
        self.add_widget(self.main_layout)

    def build_content(self):
        self.main_layout.clear_widgets()

        top = BoxLayout(orientation="horizontal", size_hint_y=0.08)
        back = Button(text="← 返回", font_size=16, background_normal="",
                       color=get_color_from_hex(THEME["text"]), size_hint_x=0.25)
        back.bind(on_release=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        top.add_widget(Label(text="🎯 学习目标", font_size=22, bold=True, color=get_color_from_hex(THEME["accent"])))
        add_btn = Button(text="+", font_size=22, background_normal="",
                          color=get_color_from_hex(THEME["success"]), size_hint_x=0.15)
        add_btn.bind(on_release=self.show_add_goal)
        top.add_widget(add_btn)
        self.main_layout.add_widget(top)

        total_xp = db.get_total_xp()
        xp_box = BoxLayout(orientation="horizontal", size_hint_y=0.06)
        xp_box.add_widget(Label(text=f"⭐ {total_xp} XP", font_size=16, color=get_color_from_hex(THEME["accent"])))
        self.main_layout.add_widget(xp_box)

        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM user_badges ub JOIN badges b ON ub.badge_id=b.id")
        badges = c.fetchall()
        conn.close()
        badge_text = "  ".join([f"{b['icon']} {b['name']}" for b in badges[:5]])
        if badge_text:
            self.main_layout.add_widget(Label(text=f"🏅 已获得: {badge_text}", font_size=13,
                                               color=get_color_from_hex(THEME["text_secondary"]), size_hint_y=0.06))

        self.scroll = ScrollView()
        self.goal_list = GridLayout(cols=1, spacing=8, size_hint_y=None, padding=[0,5,0,5])
        self.goal_list.bind(minimum_height=self.goal_list.setter("height"))
        self.scroll.add_widget(self.goal_list)
        self.main_layout.add_widget(self.scroll)

        self.load_goals()

    def load_goals(self):
        self.goal_list.clear_widgets()
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM goals WHERE status='active' ORDER BY created_at DESC")
        goals = c.fetchall()
        conn.close()

        if not goals:
            self.goal_list.add_widget(Label(text="还没有学习目标\n点击右上角 + 添加", color=get_color_from_hex(THEME["text_secondary"]),
                                             font_size=15, size_hint_y=None, height=80, halign="center"))
            return

        for g in goals:
            self.goal_list.add_widget(GoalCard(g))

    def show_add_goal(self, btn=None):
        content = BoxLayout(orientation="vertical", spacing=12, padding=15)
        content.add_widget(Label(text="目标名称:", color=get_color_from_hex(THEME["text"]), size_hint_y=0.08, halign="left"))
        title_input = RoundedInput(hint_text="例如: 每天读30页书", size_hint_y=0.08)
        content.add_widget(title_input)
        content.add_widget(Label(text="每日目标数量:", color=get_color_from_hex(THEME["text"]), size_hint_y=0.08, halign="left"))
        val_input = RoundedInput(text="1", input_filter="int", size_hint_y=0.08)
        content.add_widget(val_input)
        content.add_widget(Label(text="单位 (如: 页/次/分钟):", color=get_color_from_hex(THEME["text"]), size_hint_y=0.08, halign="left"))
        unit_input = RoundedInput(text="次", size_hint_y=0.08)
        content.add_widget(unit_input)

        popup = Popup(title="添加学习目标", content=content, size_hint=(0.85, 0.55),
                       background_color=get_color_from_hex(THEME["surface"]),
                       separator_color=get_color_from_hex(THEME["primary"]),
                       title_color=get_color_from_hex(THEME["accent"]))

        def save(btn):
            title = title_input.text.strip()
            if not title:
                return
            try:
                val = int(val_input.text)
            except:
                val = 1
            unit = unit_input.text.strip() or "次"
            conn = db.get_conn()
            c = conn.cursor()
            c.execute("""
                INSERT INTO goals (title, target_type, target_value, unit, xp_reward)
                VALUES (?, 'daily', ?, ?, ?)
            """, (title, val, unit, val * 5))
            conn.commit()
            conn.close()
            popup.dismiss()
            self.build_content()

        btn_box = BoxLayout(orientation="horizontal", spacing=15, size_hint_y=0.1)
        save_btn = Button(text="保存", background_normal="", background_color=get_color_from_hex(THEME["success"]),
                           color=(1,1,1,1))
        save_btn.bind(on_release=save)
        btn_box.add_widget(save_btn)
        cancel_btn = Button(text="取消", background_normal="", background_color=get_color_from_hex(THEME["danger"]),
                             color=(1,1,1,1))
        cancel_btn.bind(on_release=popup.dismiss)
        btn_box.add_widget(cancel_btn)
        content.add_widget(btn_box)
        popup.open()

    def on_enter(self):
        self.build_content()


class GoalCard(BoxLayout):
    def __init__(self, goal, **kwargs):
        super().__init__(**kwargs)
        self.goal_id = goal['id']
        self.target = goal['target_value']
        self.unit = goal['unit']
        self.xp_reward = goal['xp_reward']
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = 90
        self.padding = [12, 8]
        self.spacing = 4

        with self.canvas.before:
            Color(*get_color_from_hex(THEME["surface"]))
            RoundedRectangle(pos=self.pos, size=self.size, radius=[10])

        title_lbl = Label(text=goal['title'], font_size=16, color=get_color_from_hex(THEME["accent"]),
                           halign="left", size_hint_y=0.35)
        title_lbl.bind(size=title_lbl.setter("text_size"))
        self.add_widget(title_lbl)

        progress_layout = BoxLayout(orientation="horizontal", size_hint_y=0.4, spacing=10)

        current = goal['current_value']
        pct = min(current / self.target, 1.0) if self.target > 0 else 0

        pb = ProgressBar(max=1, value=pct, size_hint_x=0.6)
        pb.color = get_color_from_hex(THEME["success"])
        progress_layout.add_widget(pb)

        self.prog_label = Label(text=f"{current}/{self.target} {self.unit}", font_size=13,
                                 color=get_color_from_hex(THEME["text"]), size_hint_x=0.25)
        progress_layout.add_widget(self.prog_label)

        add_prog_btn = Button(text="+1", font_size=14, size_hint_x=0.15, background_normal="",
                               background_color=get_color_from_hex(THEME["primary"]), color=(1,1,1,1))
        add_prog_btn.bind(on_release=self.add_progress)
        progress_layout.add_widget(add_prog_btn)

        self.add_widget(progress_layout)

    def add_progress(self, btn):
        conn = db.get_conn()
        c = conn.cursor()
        c.execute("SELECT * FROM goals WHERE id=?", (self.goal_id,))
        goal = c.fetchone()
        new_val = goal['current_value'] + 1
        c.execute("UPDATE goals SET current_value=? WHERE id=?", (new_val, self.goal_id))
        db.add_xp("goal", self.goal_id, self.xp_reward)

        if new_val >= self.target:
            c.execute("UPDATE goals SET current_value=0, status='active' WHERE id=?", (self.goal_id,))
            App.get_running_app().show_popup("🎉 目标达成！", f"完成了 '{goal['title']}'!\n获得 {self.xp_reward} XP！")
        conn.commit()
        conn.close()

        App.get_running_app().root.get_screen("goals").build_content()


class StatsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.build_ui()

    def build_ui(self):
        layout = BoxLayout(orientation="vertical", spacing=10, padding=15)
        with layout.canvas.before:
            Color(*get_color_from_hex(THEME["bg"]))
            Rectangle(pos=layout.pos, size=layout.size)

        top = BoxLayout(orientation="horizontal", size_hint_y=0.08)
        back = Button(text="← 返回", font_size=16, background_normal="",
                       color=get_color_from_hex(THEME["text"]), size_hint_x=0.25)
        back.bind(on_release=lambda x: setattr(self.manager, "current", "main"))
        top.add_widget(back)
        top.add_widget(Label(text="📊 统计与成就", font_size=20, bold=True, color=get_color_from_hex(THEME["accent"])))
        top.add_widget(Label(size_hint_x=0.25))
        layout.add_widget(top)

        self.scroll = ScrollView()
        self.content = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=[0,5,0,5])
        self.content.bind(minimum_height=self.content.setter("height"))
        self.scroll.add_widget(self.content)
        layout.add_widget(self.scroll)
        self.add_widget(layout)

    def on_enter(self):
        self.refresh()

    def refresh(self):
        self.content.clear_widgets()
        conn = db.get_conn()
        c = conn.cursor()

        total_xp = db.get_total_xp()

        c.execute("SELECT COUNT(*) FROM pomodoro_sessions WHERE completed=1")
        pomo_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM tasks WHERE status='done'")
        task_done = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM tasks")
        task_total = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM books")
        book_count = c.fetchone()[0]

        c.execute("SELECT COUNT(*) FROM goals WHERE status='active'")
        goal_count = c.fetchone()[0]

        conn.close()

        stats = [
            ("⭐ 总经验值", f"{total_xp} XP"),
            ("🍅 完成番茄钟", f"{pomo_count} 个"),
            ("✅ 完成任务", f"{task_done}/{task_total}"),
            ("📚 电子书数量", f"{book_count} 本"),
            ("🎯 活跃目标", f"{goal_count} 个"),
        ]

        info_card = BoxLayout(orientation="vertical", size_hint_y=None, padding=[15,10], spacing=8)
        with info_card.canvas.before:
            Color(*get_color_from_hex(THEME["surface"]))
            RoundedRectangle(pos=info_card.pos, size=info_card.size, radius=[10])
        info_card.bind(minimum_height=info_card.setter("height"))
        info_card.add_widget(Label(text="📈 学习统计", font_size=18, bold=True, color=get_color_from_hex(THEME["accent"]),
                                    size_hint_y=None, height=30))
        for label, val in stats:
            row = BoxLayout(orientation="horizontal", size_hint_y=None, height=30)
            row.add_widget(Label(text=label, font_size=14, color=get_color_from_hex(THEME["text"]), halign="left"))
            row.add_widget(Label(text=val, font_size=14, color=get_color_from_hex(THEME["primary"]), halign="right"))
            info_card.add_widget(row)
        self.content.add_widget(info_card)

        conn = db.get_conn()
        c = conn.cursor()
        c.execute("""
            SELECT b.*, ub.unlocked_at FROM user_badges ub
            JOIN badges b ON ub.badge_id=b.id
            ORDER BY ub.unlocked_at DESC
        """)
        badges = c.fetchall()
        conn.close()

        badge_card = BoxLayout(orientation="vertical", size_hint_y=None, padding=[15,10], spacing=6)
        with badge_card.canvas.before:
            Color(*get_color_from_hex(THEME["surface"]))
            RoundedRectangle(pos=badge_card.pos, size=badge_card.size, radius=[10])
        badge_card.bind(minimum_height=badge_card.setter("height"))
        badge_card.add_widget(Label(text="🏅 已获得成就", font_size=18, bold=True,
                                     color=get_color_from_hex(THEME["accent"]), size_hint_y=None, height=30))

        if badges:
            for b in badges:
                lbl = Label(text=f"{b['icon']}  {b['name']}  -  {b['description']}", font_size=14,
                             color=get_color_from_hex(THEME["text"]), size_hint_y=None, height=25, halign="left")
                badge_card.add_widget(lbl)
        else:
            badge_card.add_widget(Label(text="还没有获得成就哦，继续加油！", font_size=14,
                                         color=get_color_from_hex(THEME["text_secondary"]), size_hint_y=None, height=25))
        self.content.add_widget(badge_card)


if __name__ == "__main__":
    try:
        import sqlite3 as sqlite3
    except:
        pass
    StudyApp().run()
