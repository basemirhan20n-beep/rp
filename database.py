import sqlite3
from datetime import date


class Database:
    def __init__(self, db_path: str = "parti.db"):
        self.db_path = db_path
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS kullanicilar (
                user_id   INTEGER PRIMARY KEY,
                username  TEXT,
                role      TEXT,
                xp        INTEGER DEFAULT 0,
                level     INTEGER DEFAULT 1,
                guven     INTEGER DEFAULT 50,
                streak    INTEGER DEFAULT 0,
                last_task TEXT DEFAULT ''
            )
        """)
        conn.commit()
        conn.close()

    def kullanici_ekle(self, user_id: int, username: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO kullanicilar (user_id, username) VALUES (?, ?)",
            (user_id, username),
        )
        conn.commit()
        conn.close()

    def kullanici_getir(self, user_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM kullanicilar WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def kullanici_username_ile_getir(self, username: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM kullanicilar WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def kullanici_guncelle(self, user_id: int, **kwargs):
        if not kwargs:
            return
        fields = ", ".join(f"{k}=?" for k in kwargs)
        values = list(kwargs.values()) + [user_id]
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(f"UPDATE kullanicilar SET {fields} WHERE user_id=?", values)
        conn.commit()
        conn.close()

    def rol_ata(self, user_id: int, rol):
        self.kullanici_guncelle(user_id, role=rol)

    def lider_tablosu(self, limit: int = 10):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT username, xp, role, guven FROM kullanicilar ORDER BY xp DESC LIMIT ?",
            (limit,),
        )
        rows = cur.fetchall()
        conn.close()
        return [(r["username"], r["xp"], r["role"], r["guven"]) for r in rows]

    def tum_kullanicilari_getir(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT user_id, username FROM kullanicilar")
        rows = cur.fetchall()
        conn.close()
        return [(r["user_id"], r["username"]) for r in rows]
