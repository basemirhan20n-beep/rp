import sqlite3
import os
from typing import Optional


class Database:
    def __init__(self, db_path: str = "parti.db"):
        self.db_path = db_path
        self._init_db()

    def _baglanti(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kullanicilar (
                user_id     INTEGER PRIMARY KEY,
                username    TEXT,
                xp          INTEGER DEFAULT 0,
                level       INTEGER DEFAULT 1,
                guven       INTEGER DEFAULT 100,
                streak      INTEGER DEFAULT 0,
                last_task   TEXT DEFAULT NULL,
                role        TEXT DEFAULT NULL,
                created_at  TEXT DEFAULT (date('now'))
            )
        """)
        conn.commit()
        conn.close()

    def kullanici_ekle(self, user_id: int, username: str):
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR IGNORE INTO kullanicilar (user_id, username)
            VALUES (?, ?)
        """, (user_id, username))
        conn.commit()
        conn.close()

    def kullanici_getir(self, user_id: int) -> Optional[dict]:
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM kullanicilar WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def kullanici_username_ile_getir(self, username: str) -> Optional[dict]:
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM kullanicilar WHERE LOWER(username) = LOWER(?)",
            (username,)
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return dict(row)
        return None

    def kullanici_guncelle(self, user_id: int, **kwargs):
        if not kwargs:
            return
        kolonlar = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        degerler = list(kwargs.values()) + [user_id]
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute(
            f"UPDATE kullanicilar SET {kolonlar} WHERE user_id = ?",
            degerler
        )
        conn.commit()
        conn.close()

    def rol_ata(self, user_id: int, rol: Optional[str]):
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE kullanicilar SET role = ? WHERE user_id = ?",
            (rol, user_id)
        )
        conn.commit()
        conn.close()

    def lider_tablosu(self) -> list:
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT username, xp, role, guven
            FROM kullanicilar
            ORDER BY xp DESC
            LIMIT 10
        """)
        rows = cursor.fetchall()
        conn.close()
        return [(r["username"], r["xp"], r["role"], r["guven"]) for r in rows]

    def tum_kullanicilari_getir(self) -> list:
        conn = self._baglanti()
        cursor = conn.cursor()
        cursor.execute("SELECT user_id, username FROM kullanicilar")
        rows = cursor.fetchall()
        conn.close()
        return [(r["user_id"], r["username"]) for r in rows]
