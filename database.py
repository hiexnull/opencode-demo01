import sqlite3
import os
from datetime import datetime


DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "studyapp.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.executescript("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            priority INTEGER DEFAULT 0,
            status TEXT DEFAULT 'pending',
            created_at TEXT DEFAULT (datetime('now','localtime')),
            completed_at TEXT,
            goal_id INTEGER REFERENCES goals(id)
        );

        CREATE TABLE IF NOT EXISTS task_tags (
            task_id INTEGER REFERENCES tasks(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (task_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS pomodoro_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER REFERENCES tasks(id),
            duration_minutes INTEGER DEFAULT 25,
            break_minutes INTEGER DEFAULT 5,
            started_at TEXT DEFAULT (datetime('now','localtime')),
            ended_at TEXT,
            completed INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            color TEXT DEFAULT '#4488FF'
        );

        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            file_path TEXT NOT NULL,
            author TEXT DEFAULT '',
            added_at TEXT DEFAULT (datetime('now','localtime')),
            last_opened_at TEXT
        );

        CREATE TABLE IF NOT EXISTS book_tags (
            book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (book_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT DEFAULT '',
            target_type TEXT DEFAULT 'daily',
            target_value INTEGER DEFAULT 1,
            current_value INTEGER DEFAULT 0,
            unit TEXT DEFAULT 'reps',
            xp_reward INTEGER DEFAULT 10,
            created_at TEXT DEFAULT (datetime('now','localtime')),
            deadline TEXT,
            status TEXT DEFAULT 'active'
        );

        CREATE TABLE IF NOT EXISTS xp_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id INTEGER,
            xp INTEGER NOT NULL,
            created_at TEXT DEFAULT (datetime('now','localtime'))
        );

        CREATE TABLE IF NOT EXISTS badges (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            icon TEXT DEFAULT 'star',
            condition_type TEXT,
            condition_value INTEGER DEFAULT 0,
            unlocked_at TEXT
        );

        CREATE TABLE IF NOT EXISTS user_badges (
            badge_id INTEGER REFERENCES badges(id) ON DELETE CASCADE,
            unlocked_at TEXT DEFAULT (datetime('now','localtime')),
            PRIMARY KEY (badge_id)
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS book_content (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            book_id INTEGER REFERENCES books(id) ON DELETE CASCADE,
            content TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS goal_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            goal_id INTEGER REFERENCES goals(id) ON DELETE CASCADE,
            date TEXT NOT NULL,
            value INTEGER DEFAULT 1,
            UNIQUE(goal_id, date)
        );
    """)
    conn.commit()

    c.execute("SELECT COUNT(*) FROM badges")
    if c.fetchone()[0] == 0:
        default_badges = [
            ('First Focus', 'Complete your first Pomodoro', 'alarm', 'pomodoro_count', 1),
            ('Focus Novice', 'Complete 10 Pomodoros', 'alarm', 'pomodoro_count', 10),
            ('Focus Pro', 'Complete 50 Pomodoros', 'alarm', 'pomodoro_count', 50),
            ('Focus Master', 'Complete 100 Pomodoros', 'alarm', 'pomodoro_count', 100),
            ('First Task', 'Complete your first task', 'checkbox', 'task_done', 1),
            ('Go-Getter', 'Complete 50 tasks', 'checkbox', 'task_done', 50),
            ('Study Star', 'Study 7 days in a row', 'calendar', 'streak', 7),
            ('Persistent', 'Study 30 days in a row', 'calendar', 'streak', 30),
            ('Junior Scholar', 'Earn 100 XP', 'star', 'xp', 100),
            ('Intermediate Scholar', 'Earn 500 XP', 'star', 'xp', 500),
            ('Senior Scholar', 'Earn 2000 XP', 'star', 'xp', 2000),
            ('Genius', 'Earn 10000 XP', 'star', 'xp', 10000),
        ]
        c.executemany(
            "INSERT INTO badges (name, description, icon, condition_type, condition_value) VALUES (?,?,?,?,?)",
            default_badges
        )
        conn.commit()

    conn.close()


def get_setting(key, default=''):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT value FROM settings WHERE key=?", (key,))
    row = c.fetchone()
    conn.close()
    return row['value'] if row else default


def set_setting(key, value):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?,?)", (key, value))
    conn.commit()
    conn.close()


def get_total_xp():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COALESCE(SUM(xp),0) FROM xp_log")
    total = c.fetchone()[0]
    conn.close()
    return total


def add_xp(source, source_id, xp):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO xp_log (source, source_id, xp) VALUES (?,?,?)", (source, source_id, xp))
    conn.commit()
    total = get_total_xp()
    c.execute("SELECT id, condition_type, condition_value FROM badges WHERE id NOT IN (SELECT badge_id FROM user_badges)")
    new_badges = []
    for badge in c.fetchall():
        ct = badge['condition_type']
        cv = badge['condition_value']
        met = False
        if ct == 'xp':
            if total >= cv:
                met = True
        elif ct == 'pomodoro_count':
            c2 = conn.cursor()
            c2.execute("SELECT COUNT(*) FROM pomodoro_sessions WHERE completed=1")
            if c2.fetchone()[0] >= cv:
                met = True
        elif ct == 'task_done':
            c2 = conn.cursor()
            c2.execute("SELECT COUNT(*) FROM tasks WHERE status='done'")
            if c2.fetchone()[0] >= cv:
                met = True
        elif ct == 'streak':
            met = True
        if met:
            new_badges.append(badge['id'])
            c.execute("INSERT OR IGNORE INTO user_badges (badge_id) VALUES (?)", (badge['id'],))
    conn.commit()
    conn.close()
    return new_badges
