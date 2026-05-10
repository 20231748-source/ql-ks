
from database.database import get_connection
from datetime import datetime


class ActivityLogModel:

    @staticmethod
    def _ensure_table():
        conn = get_connection()
        conn.execute("""
            CREATE TABLE IF NOT EXISTS activity_logs (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL,
                username    TEXT    NOT NULL,
                full_name   TEXT    NOT NULL,
                action      TEXT    NOT NULL,
                detail      TEXT,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
            )
        """)
        conn.commit()
        conn.close()

    @staticmethod
    def log(user_id: int, username: str, full_name: str, action: str, detail: str = ""):
        ActivityLogModel._ensure_table()
        conn = get_connection()
        try:
            conn.execute(
                """INSERT INTO activity_logs (user_id, username, full_name, action, detail)
                   VALUES (?, ?, ?, ?, ?)""",
                (user_id, username, full_name, action, detail)
            )
            conn.commit()
        except Exception:
            pass   
        finally:
            conn.close()

    @staticmethod
    def get_all(limit: int = 200):
        ActivityLogModel._ensure_table()
        conn = get_connection()
        rows = conn.execute("""
            SELECT id, full_name, username, action, detail, created_at
            FROM activity_logs
            ORDER BY id DESC
            LIMIT ?
        """, (limit,)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_user(user_id: int, limit: int = 100):
        ActivityLogModel._ensure_table()
        conn = get_connection()
        rows = conn.execute("""
            SELECT id, full_name, username, action, detail, created_at
            FROM activity_logs
            WHERE user_id = ?
            ORDER BY id DESC
            LIMIT ?
        """, (user_id, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def search(keyword: str, limit: int = 200):
        ActivityLogModel._ensure_table()
        conn = get_connection()
        kw = f"%{keyword}%"
        rows = conn.execute("""
            SELECT id, full_name, username, action, detail, created_at
            FROM activity_logs
            WHERE full_name LIKE ? OR username LIKE ? OR action LIKE ? OR detail LIKE ?
            ORDER BY id DESC
            LIMIT ?
        """, (kw, kw, kw, kw, limit)).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def clear_old(days: int = 90):
        ActivityLogModel._ensure_table()
        conn = get_connection()
        conn.execute(
            "DELETE FROM activity_logs WHERE created_at < datetime('now', ?)",
            (f"-{days} days",)
        )
        conn.commit()
        conn.close()