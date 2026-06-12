# -*- coding: utf-8 -*-
import os, math, sqlite3, json, re, zipfile, tempfile
from datetime import datetime, timedelta
from io import BytesIO
os.environ["KIVY_NO_CONSOLELOG"] = "1"
from kivy.config import Config
Config.set("kivy", "exit_on_escape", "0")
Config.set("graphics", "width", "400")
Config.set("graphics", "height", "720")

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
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivy.core.window import Window
from kivy.utils import get_color_from_hex
from kivy.metrics import dp, sp

import database as db
db.init_db()

try:
    from plyer import filechooser
    HAS_FILECHOOSER = True
except:
    HAS_FILECHOOSER = False

C = {
    "bg": "#2D2017", "surface": "#3D2D22", "card": "#4E3829",
    "border": "#1A0F0A", "shadow": "#1A0F0A",
    "primary": "#D4763A", "primary_dark": "#B8622E",
    "success": "#6B8F5E", "warning": "#D4A94B", "danger": "#C45A4A",
    "accent": "#8B6F9E", "text": "#F0E6D3", "text_sec": "#B8A89A",
    "text_muted": "#7A6B5E", "gold": "#FFD700",
}
BW = 2

def rgba(h, a=1):
    c = get_color_from_hex(h); return (c[0], c[1], c[2], a)

def pixel_canvas(widget, bg=None, border=True, shadow=True):
    widget.bind(pos=lambda *a: _pixel_draw(widget, bg, border, shadow),
                size=lambda *a: _pixel_draw(widget, bg, border, shadow))

def _pixel_draw(w, bg, border, shadow):
    w.canvas.before.clear()
    with w.canvas.before:
        if shadow:
            Color(*rgba(C["shadow"], 0.5))
            Rectangle(pos=(w.x + dp(2), w.y - dp(2)), size=w.size)
        if bg:
            Color(*rgba(bg))
            Rectangle(pos=w.pos, size=w.size)
        if border:
            Color(*rgba(C["border"]))
            Rectangle(pos=w.pos, size=(w.width, dp(BW)))
            Rectangle(pos=w.pos, size=(dp(BW), w.height))
            Rectangle(pos=(w.x, w.y + w.height - dp(BW)), size=(w.width, dp(BW)))
            Rectangle(pos=(w.x + w.width - dp(BW), w.y), size=(dp(BW), w.height))

class MB(Button):
    def __init__(self, text="", bg=C["primary"], fg=C["text"], **kw):
        super().__init__(**kw)
        self.text = text; self._bg = bg; self._fg = fg
        self.font_size = dp(14); self.background_normal = ""
        self.background_color = (0,0,0,0); self.color = rgba(fg)
        self.size_hint_y = None; self.height = dp(44)
        self.bind(pos=self._draw, size=self._draw)
    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*rgba(C["shadow"], 0.5))
            Rectangle(pos=(self.x + dp(2), self.y - dp(2)), size=self.size)
            Color(*rgba(self._bg))
            Rectangle(pos=self.pos, size=self.size)
            Color(*rgba(C["border"]))
            Rectangle(pos=self.pos, size=(self.width, dp(BW)))
            Rectangle(pos=self.pos, size=(dp(BW), self.height))
            Rectangle(pos=(self.x, self.y + self.height - dp(BW)), size=(self.width, dp(BW)))
            Rectangle(pos=(self.x + self.width - dp(BW), self.y), size=(dp(BW), self.height))

class ML(Label):
    def __init__(self, text="", sz=15, col=C["text"], bd=False, **kw):
        super().__init__(**kw)
        self.text = text; self.font_size = dp(sz); self.color = rgba(col)
        self.bold = bd; self.halign = "left"; self.valign = "middle"
        self.text_size = (None, None)

class MC(BoxLayout):
    def __init__(self, bg=None, **kw):
        super().__init__(**kw)
        self._bg = bg or C["card"]
        self.orientation = "vertical"; self.padding = dp(16); self.spacing = dp(8)
        self.size_hint_y = None
        self.bind(pos=self._draw, size=self._draw)
    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*rgba(C["shadow"], 0.5))
            Rectangle(pos=(self.x + dp(2), self.y - dp(2)), size=self.size)
            Color(*rgba(self._bg))
            Rectangle(pos=self.pos, size=self.size)
            Color(*rgba(C["border"]))
            Rectangle(pos=self.pos, size=(self.width, dp(BW)))
            Rectangle(pos=self.pos, size=(dp(BW), self.height))
            Rectangle(pos=(self.x, self.y + self.height - dp(BW)), size=(self.width, dp(BW)))
            Rectangle(pos=(self.x + self.width - dp(BW), self.y), size=(dp(BW), self.height))

class MI(TextInput):
    def __init__(self, hint="", **kw):
        super().__init__(**kw)
        self.hint_text = hint; self.font_size = dp(14)
        self.background_normal = ""; self.background_active = ""
        self.background_color = (0,0,0,0)
        self.foreground_color = rgba(C["text"])
        self.hint_text_color = rgba(C["text_sec"])
        self.cursor_color = rgba(C["primary"])
        self.padding = [dp(12), dp(10)]; self.size_hint_y = None; self.height = dp(44)
        self.bind(pos=self._draw, size=self._draw)
    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*rgba(C["shadow"], 0.4))
            Rectangle(pos=(self.x + dp(2), self.y - dp(2)), size=self.size)
            Color(*rgba(C["surface"]))
            Rectangle(pos=self.pos, size=self.size)
            Color(*rgba(C["border"]))
            Rectangle(pos=self.pos, size=(self.width, dp(BW)))
            Rectangle(pos=self.pos, size=(dp(BW), self.height))
            Rectangle(pos=(self.x, self.y + self.height - dp(BW)), size=(self.width, dp(BW)))
            Rectangle(pos=(self.x + self.width - dp(BW), self.y), size=(dp(BW), self.height))

class BGWidget(FloatLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.bind(pos=self._draw, size=self._draw)
    def _draw(self, *a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*rgba(C["bg"]))
            Rectangle(pos=self.pos, size=self.size)

class StudyMate(App):
    def build(self):
        self.title = "StudyMate"
        Window.clearcolor = rgba(C["bg"])
        sm = ScreenManager()
        sm.add_widget(MainScreen(name="main"))
        sm.add_widget(PomoScreen(name="pomo"))
        sm.add_widget(TodoScreen(name="todo"))
        sm.add_widget(BookScreen(name="book"))
        sm.add_widget(TagScreen(name="tags"))
        sm.add_widget(GoalScreen(name="goals"))
        sm.add_widget(StatsScreen(name="stats"))
        sm.add_widget(AchieveScreen(name="achieve"))
        return sm
    def popup(self, title, msg):
        l = BoxLayout(orientation="vertical", spacing=dp(15), padding=dp(20))
        l.add_widget(ML(msg, sz=14, halign="center", text_size=(None, None)))
        b = MB("OK", bg=C["primary"], fg=C["text"])
        l.add_widget(b)
        p = Popup(title=title, content=l, size_hint=(0.8, None), height=dp(200),
                  background=C["surface"], separator_color=rgba(C["border"]),
                  title_color=rgba(C["text"]))
        b.bind(on_release=p.dismiss)
        p.open()

surface_bg = C["surface"]

class MainScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        f = BGWidget()
        m = BoxLayout(orientation="vertical", spacing=dp(4), padding=[dp(20), dp(50), dp(20), dp(20)])
        c = MC(bg=C["surface"])
        c.add_widget(ML("StudyMate", sz=28, bd=True, col=C["primary"], halign="center", text_size=(None, None)))
        self.xl = ML("0 XP", sz=14, col=C["text_sec"], halign="center", text_size=(None, None), size_hint_y=None, height=dp(20))
        c.add_widget(self.xl)
        self.sl = ML("Streak: 0 days", sz=13, col=C["text_muted"], halign="center", text_size=(None, None), size_hint_y=None, height=dp(18))
        c.add_widget(self.sl)
        m.add_widget(c)
        m.add_widget(Label(size_hint_y=None, height=dp(16)))
        for t, s, c2 in [("Pomodoro", "pomo", C["danger"]),("Tasks", "todo", C["warning"]),
                        ("Books", "book", C["success"]),("Tags", "tags", C["accent"]),
                        ("Goals", "goals", C["primary"]),("Stats", "achieve", "#79C0FF")]:
            b = MB(t, bg=c2)
            b.bind(on_release=lambda x, s=s: setattr(self.manager, "current", s))
            m.add_widget(b)
        f.add_widget(m); self.add_widget(f)
    def on_enter(self):
        self.xl.text = f"{db.get_total_xp()} XP"
        self.sl.text = f"Streak: {calc_streak()} days"

def calc_streak():
    conn = db.get_conn(); c = conn.cursor()
    c.execute("SELECT DISTINCT date(created_at) d FROM xp_log ORDER BY d DESC")
    days = [r['d'] for r in c.fetchall()]; conn.close()
    if not days: return 0
    t = datetime.now().date()
    if days[0] != t.isoformat() and days[0] != (t - timedelta(1)).isoformat(): return 0
    s = 1
    for i in range(1, len(days)):
        if (datetime.strptime(days[i-1],"%Y-%m-%d").date() - datetime.strptime(days[i],"%Y-%m-%d").date()).days == 1: s += 1
        else: break
    return s

class PomoScreen(Screen):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.w = int(db.get_setting("pw","25"))
        self.b = int(db.get_setting("pb","5"))
        self.rem = self.w*60; self.rn=False; self.bk=False; self.sid=None; self.te=None
        f = BGWidget()
        m = BoxLayout(orientation="vertical", spacing=dp(6), padding=[dp(20), dp(30), dp(20), dp(20)])
        h = BoxLayout(size_hint_y=None, height=dp(40))
        bb = MB("Back", bg=C["card"], size_hint_x=0.3)
        bb.bind(on_release=lambda x: self._stop() or setattr(self.manager,"current","main"))
        h.add_widget(bb)
        h.add_widget(ML("Pomodoro", sz=20, bd=True, col=C["danger"], halign="center", text_size=(None,None)))
        h.add_widget(Label(size_hint_x=0.3))
        m.add_widget(h)
        self.sl = ML("Focus Time", sz=16, col=C["text"], halign="center", text_size=(None,None), size_hint_y=None, height=dp(24))
        m.add_widget(self.sl)
        self.tl = ML(self._f(self.rem), sz=64, bd=True, col=C["danger"], halign="center", text_size=(None,None), size_hint_y=None, height=dp(80))
        m.add_widget(self.tl)
        self.pb = ProgressBar(max=1, value=1, size_hint_y=None, height=dp(6))
        m.add_widget(self.pb)
        bx = BoxLayout(spacing=dp(16), size_hint_y=None, height=dp(50))
        self.sb = MB("Start", bg=C["success"])
        self.sb.bind(on_release=self._tog)
        bx.add_widget(self.sb)
        rb = MB("Reset", bg=C["danger"])
        rb.bind(on_release=self._rst)
        bx.add_widget(rb)
        m.add_widget(bx)
        m.add_widget(Label(size_hint_y=None, height=dp(8)))
        self.dc = ML("Today: 0", sz=13, col=C["text_sec"], halign="center", text_size=(None,None), size_hint_y=None, height=dp(18))
        m.add_widget(self.dc)
        f.add_widget(m); self.add_widget(f)
    def _f(self, s): return f"{s//60:02d}:{s%60:02d}"
    def _tog(self, *a):
        if not self.rn:
            if not self.sid:
                conn=db.get_conn();c=conn.cursor()
                c.execute("INSERT INTO pomodoro_sessions (duration_minutes, break_minutes) VALUES(?,?)",(self.w,self.b))
                conn.commit();self.sid=c.lastrowid;conn.close()
            self.rn=True;self.te=Clock.schedule_interval(self._tk,1)
            self.sb.text="Pause";self.sb._bg=C["warning"];self.sb._draw()
        else:
            self.rn=False
            if self.te:self.te.cancel()
            self.sb.text="Resume";self.sb._bg=C["success"];self.sb._draw()
    def _tk(self,dt):
        self.rem-=1;self.tl.text=self._f(self.rem)
        t=self.b*60 if self.bk else self.w*60
        self.pb.value=self.rem/t
        if self.rem<=0:self._done()
    def _done(self):
        if self.te:self.te.cancel();self.rn=False
        if not self.bk:
            conn=db.get_conn();c=conn.cursor()
            c.execute("UPDATE pomodoro_sessions SET completed=1,ended_at=datetime('now','localtime') WHERE id=?",(self.sid,))
            conn.commit();conn.close()
            db.add_xp("pomo",self.sid,10);self.sid=None
            self.bk=True;self.rem=self.b*60
            self.sl.text="Break Time";self.sl.color=rgba(C["success"])
            self.tl.color=rgba(C["success"])
        else:
            self.bk=False;self.rem=self.w*60
            self.sl.text="Focus Time";self.sl.color=rgba(C["text"])
            self.tl.color=rgba(C["danger"])
        self.pb.value=1;self.tl.text=self._f(self.rem)
        self.sb.text="Start";self.sb._bg=C["success"];self.sb._draw()
        self._up()
    def _rst(self,*a):
        self._stop();self.bk=False;self.rem=self.w*60;self.sid=None
        self.tl.text=self._f(self.rem);self.pb.value=1
        self.sl.text="Focus Time";self.sl.color=rgba(C["text"])
        self.tl.color=rgba(C["danger"])
        self.sb.text="Start";self.sb._bg=C["success"];self.sb._draw()
    def _stop(self):
        self.rn=False
        if self.te:self.te.cancel();self.te=None
    def _up(self):
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT COUNT(*) FROM pomodoro_sessions WHERE completed=1 AND date(ended_at)=date('now','localtime')")
        self.dc.text=f"Today: {c.fetchone()[0]}";conn.close()
    def on_enter(self):self._up()

class TodoScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        self.fl="all"
        f=BGWidget()
        m=BoxLayout(orientation="vertical",spacing=dp(4),padding=[dp(16),dp(30),dp(16),dp(16)])
        h=BoxLayout(size_hint_y=None,height=dp(40))
        bb=MB("Back",bg=C["card"],size_hint_x=0.25)
        bb.bind(on_release=lambda x:setattr(self.manager,"current","main"))
        h.add_widget(bb)
        h.add_widget(ML("Tasks",sz=20,bd=True,col=C["warning"],halign="center",text_size=(None,None)))
        h.add_widget(Label(size_hint_x=0.25))
        m.add_widget(h)
        bx=BoxLayout(spacing=dp(8),size_hint_y=None,height=dp(48))
        self.inp=MI(hint="New task...")
        bx.add_widget(self.inp)
        ab=MB("Add",bg=C["success"],size_hint_x=0.25,height=dp(48))
        ab.bind(on_release=self._add)
        bx.add_widget(ab)
        m.add_widget(bx)
        fbx=BoxLayout(spacing=dp(8),size_hint_y=None,height=dp(36))
        self.fa=MB("All",bg=C["primary"],fg=C["text"],height=dp(36))
        self.fp=MB("Pending",bg=C["card"],fg=C["text_sec"],height=dp(36))
        self.fd=MB("Done",bg=C["card"],fg=C["text_sec"],height=dp(36))
        self.fa.bind(on_release=lambda x:self._ld("all"))
        self.fp.bind(on_release=lambda x:self._ld("pending"))
        self.fd.bind(on_release=lambda x:self._ld("done"))
        fbx.add_widget(self.fa);fbx.add_widget(self.fp);fbx.add_widget(self.fd)
        m.add_widget(fbx)
        sv=ScrollView();self.gl=GridLayout(cols=1,spacing=dp(6),size_hint_y=None,padding=[0,dp(4),0,dp(4)])
        self.gl.bind(minimum_height=self.gl.setter("height"))
        sv.add_widget(self.gl);m.add_widget(sv)
        f.add_widget(m);self.add_widget(f)
    def _add(self,*a):
        t=self.inp.text.strip()
        if not t:return
        conn=db.get_conn();c=conn.cursor()
        c.execute("INSERT INTO tasks (title) VALUES(?)",(t,));conn.commit();conn.close()
        self.inp.text="";self._ld(self.fl)
    def _ld(self,f=None):
        if f:self.fl=f
        self.gl.clear_widgets()
        for b in [self.fa,self.fp,self.fd]:b._bg=C["card"];b._draw()
        [self.fa,self.fp,self.fd][["all","pending","done"].index(self.fl)]._bg=C["primary_dark"]
        conn=db.get_conn();c=conn.cursor()
        if self.fl=="all":c.execute("SELECT * FROM tasks ORDER BY status='pending' DESC, created_at DESC")
        else:c.execute("SELECT * FROM tasks WHERE status=? ORDER BY created_at DESC",(self.fl,))
        ts=c.fetchall();conn.close()
        if not ts:
            self.gl.add_widget(ML("No tasks yet",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(60)))
            return
        for t in ts:self.gl.add_widget(TodoCard(t))
    def on_enter(self):self._ld()

class TodoCard(BoxLayout):
    def __init__(self,t,**kw):
        super().__init__(**kw)
        self.tid=t['id']
        self.orientation="horizontal";self.spacing=dp(8);self.padding=[dp(10),dp(6)]
        self.size_hint_y=None;self.height=dp(56)
        self.bind(pos=self._draw,size=self._draw)
        d=t['status']=='done'
        self.cb=MB("✅" if d else "⬜",bg=C["card"],fg=C["text"],size_hint_x=0.13,height=dp(44))
        self.cb.bind(on_release=self._tog)
        self.add_widget(self.cb)
        txt=t['title'][:28]+".." if len(t['title'])>28 else t['title']
        self.lb=ML(txt,sz=15,col=C["text_sec"] if d else C["text"])
        self.add_widget(self.lb)
        xb=MB("✕",bg=C["danger"],fg=C["text"],size_hint_x=0.13,height=dp(44))
        xb.bind(on_release=self._del)
        self.add_widget(xb)
    def _draw(self,*a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*rgba(C["shadow"],0.4))
            Rectangle(pos=(self.x+dp(2),self.y-dp(2)),size=self.size)
            Color(*rgba(C["surface"]))
            Rectangle(pos=self.pos,size=self.size)
            Color(*rgba(C["border"]))
            Rectangle(pos=self.pos,size=(self.width,dp(1)))
            Rectangle(pos=self.pos,size=(dp(1),self.height))
            Rectangle(pos=(self.x,self.y+self.height-dp(1)),size=(self.width,dp(1)))
            Rectangle(pos=(self.x+self.width-dp(1),self.y),size=(dp(1),self.height))
    def _tog(self,*a):
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT status FROM tasks WHERE id=?",(self.tid,))
        r=c.fetchone()
        if r['status']=='done':
            c.execute("UPDATE tasks SET status='pending',completed_at=NULL WHERE id=?",(self.tid,))
            self.cb.text="⬜"
        else:
            c.execute("UPDATE tasks SET status='done',completed_at=datetime('now','localtime') WHERE id=?",(self.tid,))
            db.add_xp("task",self.tid,5)
            self.cb.text="✅"
        conn.commit();conn.close()
        App.get_running_app().root.get_screen("todo")._ld()
    def _del(self,*a):
        conn=db.get_conn();c=conn.cursor()
        c.execute("DELETE FROM tasks WHERE id=?",(self.tid,));conn.commit();conn.close()
        App.get_running_app().root.get_screen("todo")._ld()

class BookScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        f=BGWidget()
        m=BoxLayout(orientation="vertical",spacing=dp(6),padding=[dp(16),dp(30),dp(16),dp(16)])
        h=BoxLayout(size_hint_y=None,height=dp(40))
        bb=MB("Back",bg=C["card"],size_hint_x=0.25)
        bb.bind(on_release=lambda x:setattr(self.manager,"current","main"))
        h.add_widget(bb)
        h.add_widget(ML("Books",sz=20,bd=True,col=C["success"],halign="center",text_size=(None,None)))
        h.add_widget(Label(size_hint_x=0.25))
        m.add_widget(h)
        bx=BoxLayout(spacing=dp(8),size_hint_y=None,height=dp(48))
        self.inp=MI(hint="Search title or online...")
        bx.add_widget(self.inp)
        sb=MB("Search",bg=C["success"],fg=C["text"],size_hint_x=0.22,height=dp(48))
        sb.bind(on_release=self._srch)
        bx.add_widget(sb)
        ib=MB("Import",bg=C["accent"],fg=C["text"],size_hint_x=0.18,height=dp(48))
        ib.bind(on_release=self._imp)
        bx.add_widget(ib)
        m.add_widget(bx)
        tb=BoxLayout(spacing=dp(8),size_hint_y=None,height=dp(36))
        self.tb1=MB("Local",bg=C["primary"],fg=C["text"],height=dp(36))
        self.tb2=MB("Online",bg=C["card"],fg=C["text_sec"],height=dp(36))
        self._mode="local"
        self.tb1.bind(on_release=lambda x:self._sw("local"))
        self.tb2.bind(on_release=lambda x:self._sw("online"))
        tb.add_widget(self.tb1);tb.add_widget(self.tb2)
        m.add_widget(tb)
        sv=ScrollView();self.gl=GridLayout(cols=1,spacing=dp(6),size_hint_y=None,padding=[0,dp(4),0,dp(4)])
        self.gl.bind(minimum_height=self.gl.setter("height"))
        sv.add_widget(self.gl);m.add_widget(sv)
        f.add_widget(m);self.add_widget(f)
    def _sw(self,mode):
        self._mode=mode
        self.tb1._bg=C["primary"] if mode=="local" else C["card"]
        self.tb2._bg=C["primary"] if mode=="online" else C["card"]
        self.tb1._draw();self.tb2._draw()
        self.gl.clear_widgets()
        if mode=="local":self._list_books()
        else:self.gl.add_widget(ML("Enter keywords and tap Search",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(50)))
    def _list_books(self):
        self.gl.clear_widgets()
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT * FROM books ORDER BY added_at DESC")
        bs=c.fetchall();conn.close()
        if not bs:
            self.gl.add_widget(ML("No books imported yet",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(50)))
            return
        for bk in bs:
            cd=MC()
            cd.add_widget(ML(bk['title'],sz=16,bd=True,col=C["success"]))
            a=bk['author'] or "Unknown"
            cd.add_widget(ML(f"Author: {a}",sz=13,col=C["text_sec"]))
            self.gl.add_widget(cd)
    def _srch(self,*a):
        kw=self.inp.text.strip().lower()
        self.gl.clear_widgets()
        if not kw:
            self.gl.add_widget(ML("Enter a keyword",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(50)))
            return
        if self._mode=="online":
            self._search_web(kw)
        else:
            self._search_local(kw)
    def _search_local(self,kw):
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT * FROM books WHERE LOWER(title) LIKE ? OR LOWER(author) LIKE ?",(f"%{kw}%",f"%{kw}%"))
        bs=c.fetchall()
        if not bs:
            c.execute("SELECT DISTINCT b.* FROM books b JOIN book_content bc ON b.id=bc.book_id WHERE bc.content LIKE ?",(f"%{kw}%",))
            bs=c.fetchall()
        conn.close()
        if not bs:
            self.gl.add_widget(ML("No matches found",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(50)))
            return
        for bk in bs:
            cd=MC()
            cd.add_widget(ML(bk['title'],sz=16,bd=True,col=C["success"]))
            a=bk['author'] or "Unknown"
            cd.add_widget(ML(f"Author: {a}",sz=13,col=C["text_sec"]))
            self.gl.add_widget(cd)
    def _search_web(self,kw):
        self.gl.add_widget(ML("Searching online...",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(50)))
        try:
            import urllib.parse, urllib.request
            url=f"https://www.googleapis.com/books/v1/volumes?q={urllib.parse.quote(kw)}&maxResults=10"
            r=urllib.request.urlopen(url,timeout=10)
            data=json.loads(r.read())
            self.gl.clear_widgets()
            items=data.get('items',[])
            if not items:
                self.gl.add_widget(ML("No results found",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(50)))
                return
            for item in items:
                vi=item.get('volumeInfo',{})
                cd=MC()
                t=vi.get('title','Untitled')
                cd.add_widget(ML(t,sz=16,bd=True,col=C["success"]))
                aus=', '.join(vi.get('authors',['Unknown']))
                cd.add_widget(ML(f"Author: {aus}",sz=13,col=C["text_sec"]))
                desc=vi.get('description','')
                if desc:
                    cd.add_widget(ML(desc[:80]+"...",sz=12,col=C["text_muted"]))
                self.gl.add_widget(cd)
        except Exception as e:
            self.gl.clear_widgets()
            self.gl.add_widget(ML(f"Search failed: {str(e)[:40]}",sz=14,col=C["danger"],halign="center",size_hint_y=None,height=dp(50)))
    def _imp(self,*a):
        if not HAS_FILECHOOSER:
            self._manual_import()
            return
        try:
            filechooser.open_file(on_selection=self._file_selected)
        except:
            self._manual_import()
    def _manual_import(self):
        l=BoxLayout(orientation="vertical",spacing=dp(12),padding=dp(16))
        l.add_widget(ML("Title:",sz=14,col=C["text"]))
        ti=MI(hint="Enter title")
        l.add_widget(ti)
        l.add_widget(ML("Author:",sz=14,col=C["text"]))
        ai=MI(hint="Enter author")
        l.add_widget(ai)
        p=Popup(title="Import Book",content=l,size_hint=(0.85,0.45),background=C["surface"],
                separator_color=rgba(C["border"]),title_color=rgba(C["text"]))
        def sv(*a):
            t=ti.text.strip() or "Untitled"
            a2=ai.text.strip() or "Unknown"
            conn=db.get_conn();c=conn.cursor()
            c.execute("INSERT INTO books (title,author,file_path) VALUES(?,?,?)",(t,a2,"manual"))
            conn.commit();conn.close()
            p.dismiss();self._list_books()
            App.get_running_app().popup("Success",f"Added: {t}")
        bb=BoxLayout(spacing=dp(12),size_hint_y=None,height=dp(44))
        svb=MB("Save",bg=C["success"],fg=C["text"])
        svb.bind(on_release=sv)
        bb.add_widget(svb)
        cvb=MB("Cancel",bg=C["danger"],fg=C["text"])
        cvb.bind(on_release=p.dismiss)
        bb.add_widget(cvb)
        l.add_widget(bb);p.open()
    def _file_selected(self,selection):
        if not selection:return
        path=selection[0]
        name=os.path.splitext(os.path.basename(path))[0]
        conn=db.get_conn();c=conn.cursor()
        c.execute("INSERT INTO books (title,file_path) VALUES(?,?)",(name,path))
        bid=c.lastrowid
        content=""
        try:
            if path.endswith('.txt'):
                with open(path,'r',encoding='utf-8',errors='replace') as f:
                    content=f.read()
            elif path.endswith('.epub'):
                try:
                    import html2text
                    with zipfile.ZipFile(path) as z:
                        for fn in z.namelist():
                            if fn.endswith('.xhtml') or fn.endswith('.html'):
                                html=z.read(fn).decode('utf-8',errors='replace')
                                content+=html2text.html2text(html)
                except:
                    pass
            if content:
                c.execute("INSERT INTO book_content (book_id,content) VALUES(?,?)",(bid,content[:50000]))
        except:
            pass
        conn.commit();conn.close()
        self._list_books()
        App.get_running_app().popup("Success",f"Imported: {name}")
    def on_enter(self):
        self.gl.clear_widgets()
        if self._mode=="local":self._list_books()
        else:self.gl.add_widget(ML("Enter keywords and tap Search",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(50)))

class TagScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        f=BGWidget()
        m=BoxLayout(orientation="vertical",spacing=dp(8),padding=[dp(16),dp(30),dp(16),dp(16)])
        h=BoxLayout(size_hint_y=None,height=dp(40))
        bb=MB("Back",bg=C["card"],size_hint_x=0.25)
        bb.bind(on_release=lambda x:setattr(self.manager,"current","main"))
        h.add_widget(bb)
        h.add_widget(ML("Tags",sz=20,bd=True,col=C["accent"],halign="center",text_size=(None,None)))
        h.add_widget(Label(size_hint_x=0.25))
        m.add_widget(h)
        bx=BoxLayout(spacing=dp(8),size_hint_y=None,height=dp(48))
        self.inp=MI(hint="New tag name...")
        bx.add_widget(self.inp)
        ab=MB("Add",bg=C["accent"],size_hint_x=0.25,height=dp(48))
        ab.bind(on_release=self._add)
        bx.add_widget(ab)
        m.add_widget(bx)
        sv=ScrollView();self.gl=GridLayout(cols=2,spacing=dp(8),size_hint_y=None,padding=[0,dp(4),0,dp(4)])
        self.gl.bind(minimum_height=self.gl.setter("height"))
        sv.add_widget(self.gl);m.add_widget(sv)
        f.add_widget(m);self.add_widget(f)
    def _add(self,*a):
        n=self.inp.text.strip()
        if not n:return
        conn=db.get_conn();c=conn.cursor()
        try:c.execute("INSERT INTO tags (name) VALUES(?)",(n,));conn.commit()
        except sqlite3.IntegrityError:pass
        conn.close();self.inp.text="";self._ld()
    def _ld(self):
        self.gl.clear_widgets()
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT t.*,(SELECT COUNT(*) FROM task_tags WHERE tag_id=t.id)+(SELECT COUNT(*) FROM book_tags WHERE tag_id=t.id) as cnt FROM tags t ORDER BY cnt DESC")
        ts=c.fetchall();conn.close()
        if not ts:
            self.gl.add_widget(ML("No tags",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(60)))
            return
        for t in ts:
            cd=MC()
            n=t['name'][:10]+".." if len(t['name'])>10 else t['name']
            cd.add_widget(ML(f"#{n}",sz=16,bd=True,col=C["accent"],halign="center"))
            cd.add_widget(ML(f"Used {t['cnt']}x",sz=12,col=C["text_sec"],halign="center"))
            self.gl.add_widget(cd)
    def on_enter(self):self._ld()

class GoalScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        self.f=BGWidget()
        self._build()
        self.add_widget(self.f)
    def _build(self):
        self.f.clear_widgets()
        m=BoxLayout(orientation="vertical",spacing=dp(6),padding=[dp(16),dp(30),dp(16),dp(16)])
        h=BoxLayout(size_hint_y=None,height=dp(40))
        bb=MB("Back",bg=C["card"],size_hint_x=0.25)
        bb.bind(on_release=lambda x:setattr(self.manager,"current","main"))
        h.add_widget(bb)
        h.add_widget(ML("Goals",sz=20,bd=True,col=C["primary"],halign="center",text_size=(None,None)))
        ab=MB("+",bg=C["success"],fg=C["text"],size_hint_x=0.12,height=dp(36))
        ab.bind(on_release=self._add_goal)
        h.add_widget(ab)
        m.add_widget(h)
        m.add_widget(ML(f"⭐ {db.get_total_xp()} XP",sz=14,col=C["accent"],halign="center",text_size=(None,None),size_hint_y=None,height=dp(20)))
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT * FROM user_badges ub JOIN badges b ON ub.badge_id=b.id")
        bs=c.fetchall();conn.close()
        if bs:
            m.add_widget(ML("  ".join([f"{b['name']}" for b in bs[:4]]),sz=12,col=C["text_sec"],halign="center",text_size=(None,None),size_hint_y=None,height=dp(18)))
        sv=ScrollView();self.gl=GridLayout(cols=1,spacing=dp(8),size_hint_y=None,padding=[0,dp(4),0,dp(4)])
        self.gl.bind(minimum_height=self.gl.setter("height"))
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT * FROM goals WHERE status='active' ORDER BY created_at DESC")
        gs=c.fetchall();conn.close()
        if not gs:
            self.gl.add_widget(ML("No goals yet\nTap + to add one",sz=14,col=C["text_sec"],halign="center",size_hint_y=None,height=dp(80)))
        else:
            for g in gs:self.gl.add_widget(GoalCard(g))
        sv.add_widget(self.gl);m.add_widget(sv)
        self.f.add_widget(m)
    def _add_goal(self,*a):
        l=BoxLayout(orientation="vertical",spacing=dp(12),padding=dp(16))
        l.add_widget(ML("Goal name:",sz=14,col=C["text"]))
        ti=MI(hint="e.g. Read 30 pages daily")
        l.add_widget(ti)
        l.add_widget(ML("Daily target:",sz=14,col=C["text"]))
        vi=MI(hint="30")
        l.add_widget(vi)
        l.add_widget(ML("Unit (pages/reps/min):",sz=14,col=C["text"]))
        ui=MI(hint="pages")
        l.add_widget(ui)
        p=Popup(title="New Goal",content=l,size_hint=(0.85,0.55),background=C["surface"],
                separator_color=rgba(C["border"]),title_color=rgba(C["text"]))
        def sv(*a):
            t=ti.text.strip()
            if not t:return
            try:v=int(vi.text) if vi.text.strip() else 1
            except:v=1
            u=ui.text.strip() or "reps"
            conn=db.get_conn();c=conn.cursor()
            c.execute("INSERT INTO goals(title,target_type,target_value,unit,xp_reward) VALUES(?,'daily',?,?,?)",(t,v,u,v*5))
            conn.commit();conn.close();p.dismiss();self._build()
        bb=BoxLayout(spacing=dp(12),size_hint_y=None,height=dp(44))
        svb=MB("Save",bg=C["success"],fg=C["text"])
        svb.bind(on_release=sv)
        bb.add_widget(svb)
        cvb=MB("Cancel",bg=C["danger"],fg=C["text"])
        cvb.bind(on_release=p.dismiss)
        bb.add_widget(cvb)
        l.add_widget(bb);p.open()
    def on_enter(self):self._build()

class GoalCard(BoxLayout):
    def __init__(self,g,**kw):
        super().__init__(**kw)
        self.gid=g['id'];self.tg=g['target_value'];self.un=g['unit'];self.xp=g['xp_reward']
        self.orientation="vertical";self.padding=dp(16);self.spacing=dp(4)
        self.size_hint_y=None;self.height=dp(110)
        self.bind(pos=self._draw,size=self._draw)
        self.add_widget(ML(g['title'],sz=16,bd=True,col=C["primary"]))
        cur=g['current_value'];pct=min(cur/self.tg,1) if self.tg>0 else 0
        pb=BoxLayout(spacing=dp(10),size_hint_y=None,height=dp(24))
        pgb=ProgressBar(max=1,value=pct,size_hint_x=0.5,height=dp(24))
        pb.add_widget(pgb)
        pb.add_widget(ML(f"{cur}/{self.tg} {self.un}",sz=13,col=C["text"],size_hint_x=0.2))
        apb=MB("+1",bg=C["primary"],fg=C["text"],size_hint_x=0.12,height=dp(24))
        apb.bind(on_release=self._inc)
        pb.add_widget(apb)
        self.add_widget(pb)
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT COUNT(*) FROM goal_log WHERE goal_id=? AND date=date('now','localtime')",(self.gid,))
        today_done=c.fetchone()[0]
        c.execute("SELECT DISTINCT date FROM goal_log WHERE goal_id=? ORDER BY date DESC",(self.gid,))
        dates=[r['date'] for r in c.fetchall()]
        conn.close()
        streak=0
        d=datetime.now().date()
        for i,ds in enumerate(dates):
            dd=datetime.strptime(ds,"%Y-%m-%d").date()
            if i==0:
                if dd!=d and dd!=(d-timedelta(1)):break
            if (d-timedelta(i)).isoformat()==ds:streak+=1
            else:break
        status="✅ Checked in" if today_done>0 else "⬜ Not checked in"
        self.add_widget(ML(f"{status} | {streak} day streak",sz=12,col=C["text_sec"]))
    def _draw(self,*a):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*rgba(C["shadow"],0.5))
            Rectangle(pos=(self.x+dp(2),self.y-dp(2)),size=self.size)
            Color(*rgba(C["card"]))
            Rectangle(pos=self.pos,size=self.size)
            Color(*rgba(C["border"]))
            Rectangle(pos=self.pos,size=(self.width,dp(BW)))
            Rectangle(pos=self.pos,size=(dp(BW),self.height))
            Rectangle(pos=(self.x,self.y+self.height-dp(BW)),size=(self.width,dp(BW)))
            Rectangle(pos=(self.x+self.width-dp(BW),self.y),size=(dp(BW),self.height))
    def _inc(self,*a):
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT * FROM goals WHERE id=?",(self.gid,))
        g=c.fetchone();nv=g['current_value']+1
        c.execute("UPDATE goals SET current_value=? WHERE id=?",(nv,self.gid))
        db.add_xp("goal",self.gid,self.xp)
        today=datetime.now().date().isoformat()
        c.execute("INSERT OR IGNORE INTO goal_log(goal_id,date) VALUES(?,?)",(self.gid,today))
        if nv>=self.tg:
            c.execute("UPDATE goals SET current_value=0 WHERE id=?",(self.gid,))
        conn.commit();conn.close()
        App.get_running_app().root.get_screen("goals")._build()

class StatsScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        self.build_ui()
    def build_ui(self):
        f=BGWidget()
        m=BoxLayout(orientation="vertical",spacing=dp(8),padding=[dp(16),dp(30),dp(16),dp(16)])
        h=BoxLayout(size_hint_y=None,height=dp(40))
        bb=MB("Back",bg=C["card"],size_hint_x=0.25)
        bb.bind(on_release=lambda x:setattr(self.manager,"current","main"))
        h.add_widget(bb)
        h.add_widget(ML("Achievements",sz=20,bd=True,col="#79C0FF",halign="center",text_size=(None,None)))
        h.add_widget(Label(size_hint_x=0.25))
        m.add_widget(h)
        sv=ScrollView();self.gl=GridLayout(cols=1,spacing=dp(8),size_hint_y=None,padding=[0,dp(4),0,dp(4)])
        self.gl.bind(minimum_height=self.gl.setter("height"))
        sv.add_widget(self.gl);m.add_widget(sv)
        f.add_widget(m);self.add_widget(f)
    def on_enter(self):
        self.gl.clear_widgets()
        conn=db.get_conn();c=conn.cursor()
        tx=db.get_total_xp()
        c.execute("SELECT COUNT(*) FROM pomodoro_sessions WHERE completed=1");pc=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks WHERE status='done'");td=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks");tt=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM books");bc=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM goals WHERE status='active'");gc=c.fetchone()[0]
        conn.close()
        cd=MC()
        cd.add_widget(ML("Stats Overview",sz=18,bd=True,col=C["text"]))
        for lbl,val in [("Total XP",f"{tx} XP"),("Pomodoros",f"{pc}"),("Tasks Done",f"{td}/{tt}"),("Books",f"{bc}"),("Active Goals",f"{gc}")]:
            r=BoxLayout(spacing=dp(8),size_hint_y=None,height=dp(28))
            r.add_widget(ML(lbl,sz=14,col=C["text_sec"]))
            r.add_widget(ML(val,sz=14,bd=True,col=C["text"],halign="right"))
            cd.add_widget(r)
        self.gl.add_widget(cd)
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT b.*,ub.unlocked_at FROM user_badges ub JOIN badges b ON ub.badge_id=b.id ORDER BY ub.unlocked_at DESC")
        bs=c.fetchall();conn.close()
        bd=MC()
        bd.add_widget(ML("Earned Badges",sz=18,bd=True,col=C["text"]))
        if bs:
            for b in bs:
                bd.add_widget(ML(f"{b['name']} - {b['description']}",sz=13,col=C["text"]))
        else:bd.add_widget(ML("No badges yet. Keep going!",sz=13,col=C["text_sec"]))
        self.gl.add_widget(bd)
        cb=MB("View All Badges",bg=C["primary"])
        cb.bind(on_release=lambda x:setattr(self.manager,"current","achieve"))
        self.gl.add_widget(cb)

class AchieveScreen(Screen):
    def __init__(self,**kw):
        super().__init__(**kw)
        f=BGWidget()
        m=BoxLayout(orientation="vertical",spacing=dp(8),padding=[dp(16),dp(30),dp(16),dp(16)])
        h=BoxLayout(size_hint_y=None,height=dp(40))
        bb=MB("Back",bg=C["card"],size_hint_x=0.25)
        bb.bind(on_release=lambda x:setattr(self.manager,"current","stats"))
        h.add_widget(bb)
        h.add_widget(ML("All Badges",sz=20,bd=True,col=C["gold"],halign="center",text_size=(None,None)))
        h.add_widget(Label(size_hint_x=0.25))
        m.add_widget(h)
        self.sv=ScrollView();self.gl=GridLayout(cols=2,spacing=dp(8),size_hint_y=None,padding=[0,dp(4),0,dp(4)])
        self.gl.bind(minimum_height=self.gl.setter("height"))
        self.sv.add_widget(self.gl);m.add_widget(self.sv)
        f.add_widget(m);self.add_widget(f)
    def on_enter(self):
        self.gl.clear_widgets()
        conn=db.get_conn();c=conn.cursor()
        c.execute("SELECT * FROM badges ORDER BY id")
        all_badges=c.fetchall()
        total_xp=db.get_total_xp()
        c.execute("SELECT COUNT(*) FROM pomodoro_sessions WHERE completed=1");pc=c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM tasks WHERE status='done'");td=c.fetchone()[0]
        c.execute("SELECT badge_id FROM user_badges")
        owned={r['badge_id'] for r in c.fetchall()}
        conn.close()
        for b in all_badges:
            unlocked=b['id'] in owned
            cd=MC()
            cd.size_hint_y=None;cd.height=dp(100)
            cd.add_widget(ML(b['name'],sz=14,bd=True,col=C["gold"] if unlocked else C["text_muted"],halign="center"))
            cd.add_widget(ML(b['description'],sz=11,col=C["text_sec"] if unlocked else C["text_muted"],halign="center"))
            if not unlocked:
                ct=b['condition_type'];cv=b['condition_value']
                if ct=='xp':prog=f"{total_xp}/{cv}"
                elif ct=='pomodoro_count':prog=f"{pc}/{cv}"
                elif ct=='task_done':prog=f"{td}/{cv}"
                else:prog="?"
                cd.add_widget(ML(prog,sz=12,col=C["text_muted"],halign="center"))
            cd.bind(on_touch_down=lambda inst,touch,b=b,unlocked=unlocked:self._show_detail(inst,touch,b,unlocked))
            self.gl.add_widget(cd)
    def _show_detail(self,inst,touch,b,unlocked):
        if inst.collide_point(*touch.pos):
            msg=f"{b['name']}\n\n{b['description']}"
            if unlocked:msg+="\n\n✅ Unlocked"
            else:
                ct=b['condition_type'];cv=b['condition_value']
                h=""
                if ct=='xp':h=f"Earn {cv} XP"
                elif ct=='pomodoro_count':h=f"Complete {cv} Pomodoros"
                elif ct=='task_done':h=f"Complete {cv} tasks"
                elif ct=='streak':h=f"Study {cv} days in a row"
                msg+=f"\n\n🔒 Locked\nCondition: {h}"
            App.get_running_app().popup(b['name'],msg)

if __name__=="__main__":
    StudyMate().run()
