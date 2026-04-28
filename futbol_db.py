"""
FutbolDB — SQLite backend for Cumhuriyet Süper Ligi
"""
import sqlite3
import random
from datetime import date


ISIMLER = [
    "Ahmet", "Mehmet", "Ali", "Hasan", "Hüseyin", "İbrahim", "Mustafa",
    "Ömer", "Yusuf", "Murat", "Emre", "Burak", "Serkan", "Kemal", "Tarık",
    "Oğuz", "Cem", "Berk", "Kaan", "Arda", "Selim", "Tolga", "Uğur", "Volkan",
]
SOYISIMLER = [
    "Yılmaz", "Kaya", "Demir", "Çelik", "Şahin", "Doğan", "Arslan", "Koç",
    "Kurt", "Aydın", "Özdemir", "Erdoğan", "Çetin", "Güneş", "Polat",
    "Yıldız", "Karahan", "Bulut", "Tekin", "Aslan",
]
POZISYONLAR = ["Kaleci", "Defans", "Orta Saha", "Forvet"]
TAKTIKLER = ["4-4-2", "4-3-3", "3-5-2", "5-3-2", "4-2-3-1"]

TAKTIK_AVANTAJ = {
    ("4-3-3", "4-4-2"): 3,
    ("4-4-2", "3-5-2"): 3,
    ("3-5-2", "4-3-3"): 3,
    ("5-3-2", "4-3-3"): 2,
    ("4-2-3-1", "4-4-2"): 2,
}


def _rastgele_isim():
    return f"{random.choice(ISIMLER)} {random.choice(SOYISIMLER)}"


class FutbolDB:
    def __init__(self, db_path: str = "parti.db"):
        self.db_path = db_path
        self.TAKTIKLER = TAKTIKLER
        self._init_db()
        self._seed_players()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS takimlar (
                takim_id    INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER UNIQUE,
                isim        TEXT,
                lig_id      INTEGER DEFAULT 1,
                puan        INTEGER DEFAULT 0,
                galibiyet   INTEGER DEFAULT 0,
                beraberlik  INTEGER DEFAULT 0,
                maglubiyet  INTEGER DEFAULT 0,
                atilan_gol  INTEGER DEFAULT 0,
                yenilen_gol INTEGER DEFAULT 0,
                mac_sayisi  INTEGER DEFAULT 0,
                taktik      TEXT DEFAULT '4-4-2',
                lonca_id    INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS oyuncular (
                oyuncu_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                isim        TEXT,
                pozisyon    TEXT,
                guc         INTEGER,
                takim_id    INTEGER,
                satista     INTEGER DEFAULT 0,
                satis_fiyati INTEGER DEFAULT 0,
                gol         INTEGER DEFAULT 0,
                asist       INTEGER DEFAULT 0,
                sari_kart   INTEGER DEFAULT 0,
                kirmizi_kart INTEGER DEFAULT 0,
                sakatlik_mac INTEGER DEFAULT 0,
                son_antrenman TEXT DEFAULT ''
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS fikstur (
                mac_id      INTEGER PRIMARY KEY AUTOINCREMENT,
                lig_id      INTEGER,
                hafta       INTEGER,
                ev_takim_id INTEGER,
                dep_takim_id INTEGER,
                ev_gol      INTEGER,
                dep_gol     INTEGER,
                oynanmis    INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS kullanici_para (
                user_id INTEGER PRIMARY KEY,
                para    INTEGER DEFAULT 100000
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS loncalar (
                lonca_id INTEGER PRIMARY KEY AUTOINCREMENT,
                isim     TEXT UNIQUE,
                kurucu   INTEGER,
                puan     INTEGER DEFAULT 0
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS lonca_uyeler (
                user_id  INTEGER PRIMARY KEY,
                lonca_id INTEGER
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS daily_spin (
                user_id   INTEGER PRIMARY KEY,
                son_cark  TEXT DEFAULT ''
            )
        """)

        conn.commit()
        conn.close()

    def _seed_players(self):
        """Populate the market with free agents if empty."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM oyuncular WHERE takim_id IS NULL")
        count = cur.fetchone()[0]
        conn.close()
        if count < 50:
            conn = self._get_conn()
            cur = conn.cursor()
            for _ in range(100):
                poz = random.choice(POZISYONLAR)
                guc = random.randint(40, 85)
                fiyat = guc * random.randint(800, 1500)
                cur.execute(
                    "INSERT INTO oyuncular (isim, pozisyon, guc, takim_id, satista, satis_fiyati) VALUES (?,?,?,NULL,1,?)",
                    (_rastgele_isim(), poz, guc, fiyat),
                )
            conn.commit()
            conn.close()

    # ------------------------------------------------------------------
    # Para
    # ------------------------------------------------------------------

    def para_getir(self, user_id: int) -> int:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO kullanici_para (user_id) VALUES (?)", (user_id,)
        )
        cur.execute("SELECT para FROM kullanici_para WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        conn.commit()
        conn.close()
        return row["para"] if row else 100000

    def para_guncelle(self, user_id: int, miktar: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO kullanici_para (user_id) VALUES (?)", (user_id,)
        )
        cur.execute(
            "UPDATE kullanici_para SET para=MAX(0, para+?) WHERE user_id=?",
            (miktar, user_id),
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Takım
    # ------------------------------------------------------------------

    def takim_kur(self, user_id: int, isim: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT takim_id FROM takimlar WHERE user_id=?", (user_id,))
        if cur.fetchone():
            conn.close()
            return False, "Zaten bir takımın var."
        cur.execute(
            "INSERT INTO takimlar (user_id, isim) VALUES (?, ?)", (user_id, isim)
        )
        conn.commit()
        conn.close()
        self.para_getir(user_id)
        return True, "Takım kuruldu."

    def takim_user(self, user_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM takimlar WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def takim_id(self, takim_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM takimlar WHERE takim_id=?", (takim_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def takim_sayisi(self) -> int:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM takimlar")
        count = cur.fetchone()[0]
        conn.close()
        return count

    def tum_takimlar(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM takimlar ORDER BY puan DESC, (atilan_gol - yenilen_gol) DESC"
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def takim_gucu(self, takim_id: int) -> float:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT AVG(guc) FROM oyuncular WHERE takim_id=? AND sakatlik_mac=0",
            (takim_id,),
        )
        row = cur.fetchone()
        conn.close()
        return row[0] or 50.0

    def taktik_degistir(self, takim_id: int, taktik: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE takimlar SET taktik=? WHERE takim_id=?", (taktik, takim_id)
        )
        conn.commit()
        conn.close()

    # ------------------------------------------------------------------
    # Oyuncular / Transfer
    # ------------------------------------------------------------------

    def takim_oyunculari(self, takim_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM oyuncular WHERE takim_id=?", (takim_id,))
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def transfer_acik_mi(self) -> bool:
        """Transfer window: open on days 1-7 and 15-21 of each month."""
        gun = date.today().day
        return 1 <= gun <= 7 or 15 <= gun <= 21

    def piyasa(self, sayfa: int = 0, sayfa_boyut: int = 8):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM oyuncular WHERE satista=1")
        toplam = cur.fetchone()[0]
        cur.execute(
            "SELECT * FROM oyuncular WHERE satista=1 ORDER BY guc DESC LIMIT ? OFFSET ?",
            (sayfa_boyut, sayfa * sayfa_boyut),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows], toplam

    def satin_al(self, user_id: int, takim_id: int, oyuncu_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM oyuncular WHERE oyuncu_id=? AND satista=1", (oyuncu_id,))
        oyuncu = cur.fetchone()
        if not oyuncu:
            conn.close()
            return False, "❌ Oyuncu bulunamadı veya satışta değil."
        cur.execute("SELECT COUNT(*) FROM oyuncular WHERE takim_id=?", (takim_id,))
        if cur.fetchone()[0] >= 23:
            conn.close()
            return False, "❌ Kadro dolu (max 23 oyuncu)."
        para = self.para_getir(user_id)
        fiyat = oyuncu["satis_fiyati"]
        if para < fiyat:
            conn.close()
            return False, f"❌ Yetersiz bakiye. Gerekli: {fiyat:,}₺, Mevcut: {para:,}₺"
        # Transfer the player
        if oyuncu["takim_id"]:
            # Sell from another team → pay the selling team
            self.para_guncelle(oyuncu["takim_id"], fiyat)  # type: ignore[arg-type]
        cur.execute(
            "UPDATE oyuncular SET takim_id=?, satista=0, satis_fiyati=0 WHERE oyuncu_id=?",
            (takim_id, oyuncu_id),
        )
        conn.commit()
        conn.close()
        self.para_guncelle(user_id, -fiyat)
        return True, f"✅ *{oyuncu['isim']}* satın alındı! 💸 -{fiyat:,}₺"

    def sat(self, takim_id: int, oyuncu_id: int, fiyat: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM oyuncular WHERE oyuncu_id=? AND takim_id=?",
            (oyuncu_id, takim_id),
        )
        oyuncu = cur.fetchone()
        if not oyuncu:
            conn.close()
            return False, "❌ Bu oyuncu senin kadronunda değil."
        cur.execute(
            "UPDATE oyuncular SET satista=1, satis_fiyati=? WHERE oyuncu_id=?",
            (fiyat, oyuncu_id),
        )
        conn.commit()
        conn.close()
        return True, f"✅ *{oyuncu['isim']}* {fiyat:,}₺ fiyatıyla satışa çıkarıldı."

    def sat_iptal(self, takim_id: int, oyuncu_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM oyuncular WHERE oyuncu_id=? AND takim_id=? AND satista=1",
            (oyuncu_id, takim_id),
        )
        oyuncu = cur.fetchone()
        if not oyuncu:
            conn.close()
            return False, "❌ Satışta olan oyuncu bulunamadı."
        cur.execute(
            "UPDATE oyuncular SET satista=0, satis_fiyati=0 WHERE oyuncu_id=?",
            (oyuncu_id,),
        )
        conn.commit()
        conn.close()
        return True, f"✅ *{oyuncu['isim']}* satıştan çekildi."

    # ------------------------------------------------------------------
    # Antrenman
    # ------------------------------------------------------------------

    def antrenman_yap(self, takim_id: int):
        bugun = date.today().isoformat()
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM oyuncular WHERE takim_id=? AND son_antrenman!=? AND sakatlik_mac=0",
            (takim_id, bugun),
        )
        oyuncular = cur.fetchall()
        if not oyuncular:
            conn.close()
            return False, "Bugün zaten antrenman yapıldı veya kadro boş."
        sonuclar = []
        for o in oyuncular:
            artis = random.randint(1, 3)
            yeni_guc = min(99, o["guc"] + artis)
            cur.execute(
                "UPDATE oyuncular SET guc=?, son_antrenman=? WHERE oyuncu_id=?",
                (yeni_guc, bugun, o["oyuncu_id"]),
            )
            sonuclar.append(
                {"isim": o["isim"], "pozisyon": o["pozisyon"], "artis": artis, "yeni_guc": yeni_guc}
            )
        conn.commit()
        conn.close()
        return True, sonuclar

    # ------------------------------------------------------------------
    # Fikstür & Maç
    # ------------------------------------------------------------------

    def fikstur_var_mi(self, lig_id: int) -> bool:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fikstur WHERE lig_id=?", (lig_id,))
        count = cur.fetchone()[0]
        conn.close()
        return count > 0

    def fikstur_olustur(self, lig_id: int, sezon: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT takim_id FROM takimlar WHERE lig_id=?", (lig_id,))
        takimlar = [r[0] for r in cur.fetchall()]
        random.shuffle(takimlar)
        if len(takimlar) % 2 != 0:
            takimlar.append(None)  # bye
        n = len(takimlar)
        hafta = 1
        for rnd in range(n - 1):
            for i in range(n // 2):
                ev = takimlar[i]
                dep = takimlar[n - 1 - i]
                if ev and dep:
                    cur.execute(
                        "INSERT INTO fikstur (lig_id, hafta, ev_takim_id, dep_takim_id) VALUES (?,?,?,?)",
                        (lig_id, hafta, ev, dep),
                    )
            takimlar = [takimlar[0]] + [takimlar[-1]] + takimlar[1:-1]
            hafta += 1
        conn.commit()
        conn.close()

    def yeterli_kadro_mu(self, takim_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM oyuncular WHERE takim_id=? AND sakatlik_mac=0",
            (takim_id,),
        )
        count = cur.fetchone()[0]
        conn.close()
        if count < 11:
            return False, f"En az 11 sağlıklı oyuncu gerekli. Şu an: {count}"
        return True, ""

    def sonraki_mac(self, takim_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM fikstur WHERE (ev_takim_id=? OR dep_takim_id=?) AND oynanmis=0 ORDER BY hafta ASC LIMIT 1",
            (takim_id, takim_id),
        )
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def mac_oyna(self, mac_id: int, takim_id: int, taktik: str = "4-4-2"):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM fikstur WHERE mac_id=?", (mac_id,))
        mac = cur.fetchone()
        if not mac or mac["oynanmis"]:
            conn.close()
            return None, "Maç bulunamadı veya zaten oynandı."

        ev_id, dep_id = mac["ev_takim_id"], mac["dep_takim_id"]
        ev_takim = self.takim_id(ev_id)
        dep_takim = self.takim_id(dep_id)

        ev_guc = self.takim_gucu(ev_id) + 3  # home advantage
        dep_guc = self.takim_gucu(dep_id)

        # Tactic bonus
        ev_taktik = ev_takim.get("taktik", "4-4-2") if ev_takim else "4-4-2"
        dep_taktik = dep_takim.get("taktik", "4-4-2") if dep_takim else "4-4-2"
        ev_guc += TAKTIK_AVANTAJ.get((ev_taktik, dep_taktik), 0)
        dep_guc += TAKTIK_AVANTAJ.get((dep_taktik, ev_taktik), 0)

        # Simulate goals
        ev_gol = max(0, int(random.gauss(ev_guc / 20, 1.2)))
        dep_gol = max(0, int(random.gauss(dep_guc / 20, 1.2)))

        # Goal scorers
        ev_oyuncular = self.takim_oyunculari(ev_id)
        dep_oyuncular = self.takim_oyunculari(dep_id)

        ev_gol_atanlar = self._gol_atanlar(ev_oyuncular, ev_gol, cur)
        dep_gol_atanlar = self._gol_atanlar(dep_oyuncular, dep_gol, cur)

        # Update fixture
        cur.execute(
            "UPDATE fikstur SET ev_gol=?, dep_gol=?, oynanmis=1 WHERE mac_id=?",
            (ev_gol, dep_gol, mac_id),
        )

        # Update team stats
        self._takim_istatistik_guncelle(cur, ev_id, ev_gol, dep_gol)
        self._takim_istatistik_guncelle(cur, dep_id, dep_gol, ev_gol)

        # Prize money
        if ev_gol > dep_gol:
            self.para_guncelle(ev_takim["user_id"], 5000)
            self.para_guncelle(dep_takim["user_id"], 1000)
        elif dep_gol > ev_gol:
            self.para_guncelle(dep_takim["user_id"], 5000)
            self.para_guncelle(ev_takim["user_id"], 1000)
        else:
            self.para_guncelle(ev_takim["user_id"], 2500)
            self.para_guncelle(dep_takim["user_id"], 2500)

        # Random injuries / cards
        self._random_olaylar(ev_oyuncular + dep_oyuncular, cur)

        conn.commit()
        conn.close()

        return {
            "ev_takim": ev_takim["isim"] if ev_takim else "?",
            "dep_takim": dep_takim["isim"] if dep_takim else "?",
            "ev_gol": ev_gol,
            "dep_gol": dep_gol,
            "hafta": mac["hafta"],
            "ev_gol_atanlar": ev_gol_atanlar,
            "dep_gol_atanlar": dep_gol_atanlar,
        }, None

    def _gol_atanlar(self, oyuncular, gol_sayisi, cur):
        atanlar = []
        forvetler = [o for o in oyuncular if o["pozisyon"] == "Forvet"] or oyuncular
        for _ in range(gol_sayisi):
            if not forvetler:
                break
            scorer = random.choice(forvetler)
            atanlar.append(scorer["isim"])
            cur.execute(
                "UPDATE oyuncular SET gol=gol+1 WHERE oyuncu_id=?",
                (scorer["oyuncu_id"],),
            )
        return atanlar

    def _takim_istatistik_guncelle(self, cur, takim_id, atilan, yenilen):
        if atilan > yenilen:
            cur.execute(
                "UPDATE takimlar SET puan=puan+3, galibiyet=galibiyet+1, mac_sayisi=mac_sayisi+1, atilan_gol=atilan_gol+?, yenilen_gol=yenilen_gol+? WHERE takim_id=?",
                (atilan, yenilen, takim_id),
            )
        elif atilan == yenilen:
            cur.execute(
                "UPDATE takimlar SET puan=puan+1, beraberlik=beraberlik+1, mac_sayisi=mac_sayisi+1, atilan_gol=atilan_gol+?, yenilen_gol=yenilen_gol+? WHERE takim_id=?",
                (atilan, yenilen, takim_id),
            )
        else:
            cur.execute(
                "UPDATE takimlar SET maglubiyet=maglubiyet+1, mac_sayisi=mac_sayisi+1, atilan_gol=atilan_gol+?, yenilen_gol=yenilen_gol+? WHERE takim_id=?",
                (atilan, yenilen, takim_id),
            )

    def _random_olaylar(self, oyuncular, cur):
        for o in oyuncular:
            r = random.random()
            if r < 0.05:  # 5% injury
                mac_sayisi = random.randint(1, 3)
                cur.execute(
                    "UPDATE oyuncular SET sakatlik_mac=? WHERE oyuncu_id=?",
                    (mac_sayisi, o["oyuncu_id"]),
                )
            elif r < 0.10:  # yellow card
                cur.execute(
                    "UPDATE oyuncular SET sari_kart=sari_kart+1 WHERE oyuncu_id=?",
                    (o["oyuncu_id"],),
                )

    def son_maclar(self, takim_id: int, limit: int = 5):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT f.*, t1.isim AS ev_isim, t2.isim AS dep_isim
            FROM fikstur f
            JOIN takimlar t1 ON f.ev_takim_id = t1.takim_id
            JOIN takimlar t2 ON f.dep_takim_id = t2.takim_id
            WHERE (f.ev_takim_id=? OR f.dep_takim_id=?) AND f.oynanmis=1
            ORDER BY f.hafta DESC LIMIT ?
            """,
            (takim_id, takim_id, limit),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    def mevcut_hafta(self) -> int:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT MAX(hafta) FROM fikstur WHERE oynanmis=1")
        row = cur.fetchone()
        conn.close()
        return (row[0] or 1)

    def haftalik_fikstur(self, hafta: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT f.*, t1.isim AS ev_isim, t2.isim AS dep_isim
            FROM fikstur f
            JOIN takimlar t1 ON f.ev_takim_id = t1.takim_id
            JOIN takimlar t2 ON f.dep_takim_id = t2.takim_id
            WHERE f.hafta=?
            ORDER BY f.mac_id
            """,
            (hafta,),
        )
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Oyuncu istatistikleri
    # ------------------------------------------------------------------

    def oyuncu_istatistikleri(self, oyuncu_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM oyuncular WHERE oyuncu_id=?", (oyuncu_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    # ------------------------------------------------------------------
    # Altyapı
    # ------------------------------------------------------------------

    def altyapi_oyuncu_cikar(self, takim_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM oyuncular WHERE takim_id=?", (takim_id,))
        if cur.fetchone()[0] >= 23:
            conn.close()
            return None
        poz = random.choice(POZISYONLAR)
        guc = random.randint(30, 55)
        isim = _rastgele_isim()
        cur.execute(
            "INSERT INTO oyuncular (isim, pozisyon, guc, takim_id) VALUES (?,?,?,?)",
            (isim, poz, guc, takim_id),
        )
        oyuncu_id = cur.lastrowid
        conn.commit()
        conn.close()
        return {"oyuncu_id": oyuncu_id, "isim": isim, "pozisyon": poz, "guc": guc}

    # ------------------------------------------------------------------
    # Günlük Çark
    # ------------------------------------------------------------------

    def daily_spin(self, user_id: int):
        bugun = date.today().isoformat()
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT OR IGNORE INTO daily_spin (user_id) VALUES (?)", (user_id,)
        )
        cur.execute("SELECT son_cark FROM daily_spin WHERE user_id=?", (user_id,))
        row = cur.fetchone()
        conn.close()
        if row and row["son_cark"] == bugun:
            return None, "⏳ Bugün zaten çark çevirdin. Yarın tekrar dene!"
        oduller = [
            ("para", 5000, "💰 +5.000₺ kazandın!"),
            ("para", 10000, "💰 +10.000₺ kazandın!"),
            ("para", 2000, "💰 +2.000₺ kazandın!"),
            ("para", -1000, "💸 -1.000₺ kaybettin!"),
            ("oyuncu", None, "🌟 Altyapıdan ücretsiz oyuncu!"),
        ]
        odul = random.choice(oduller)
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE daily_spin SET son_cark=? WHERE user_id=?", (bugun, user_id)
        )
        conn.commit()
        conn.close()
        if odul[0] == "para":
            self.para_guncelle(user_id, odul[1])
        return odul[0], odul[2]

    # ------------------------------------------------------------------
    # Lonca
    # ------------------------------------------------------------------

    def lonca_kur(self, user_id: int, isim: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT lonca_id FROM lonca_uyeler WHERE user_id=?", (user_id,))
        if cur.fetchone():
            conn.close()
            return False, "❌ Zaten bir loncadasın."
        try:
            cur.execute(
                "INSERT INTO loncalar (isim, kurucu) VALUES (?,?)", (isim, user_id)
            )
            lonca_id = cur.lastrowid
            cur.execute(
                "INSERT INTO lonca_uyeler (user_id, lonca_id) VALUES (?,?)",
                (user_id, lonca_id),
            )
            conn.commit()
            conn.close()
            return True, f"✅ *{isim}* loncası kuruldu! ID: {lonca_id}"
        except sqlite3.IntegrityError:
            conn.close()
            return False, "❌ Bu isimde lonca zaten var."

    def lonca_katil(self, user_id: int, lonca_id: int) -> str:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT lonca_id FROM lonca_uyeler WHERE user_id=?", (user_id,))
        if cur.fetchone():
            conn.close()
            return "❌ Zaten bir loncadasın."
        cur.execute("SELECT * FROM loncalar WHERE lonca_id=?", (lonca_id,))
        if not cur.fetchone():
            conn.close()
            return "❌ Lonca bulunamadı."
        cur.execute(
            "INSERT INTO lonca_uyeler (user_id, lonca_id) VALUES (?,?)",
            (user_id, lonca_id),
        )
        conn.commit()
        conn.close()
        return "✅ Loncaya katıldın!"

    def lonca_listesi(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM loncalar ORDER BY puan DESC")
        rows = cur.fetchall()
        conn.close()
        return [dict(r) for r in rows]

    # ------------------------------------------------------------------
    # Kupa
    # ------------------------------------------------------------------

    def kupa_mac(self, takim_id: int):
        """Placeholder — returns None until cup fixtures are generated."""
        return None

    # ------------------------------------------------------------------
    # Sezon sıfırlama
    # ------------------------------------------------------------------

    def sezon_sifirla(self):
        conn = self._get_conn()
        cur = conn.cursor()
        # Award champion
        cur.execute(
            "SELECT takim_id, user_id, isim FROM takimlar ORDER BY puan DESC LIMIT 1"
        )
        sampiyion = cur.fetchone()
        if sampiyion:
            self.para_guncelle(sampiyion["user_id"], 50000)
        # Reset team stats
        cur.execute(
            "UPDATE takimlar SET puan=0, galibiyet=0, beraberlik=0, maglubiyet=0, atilan_gol=0, yenilen_gol=0, mac_sayisi=0"
        )
        # Clear fixtures
        cur.execute("DELETE FROM fikstur")
        # Heal all players
        cur.execute("UPDATE oyuncular SET sakatlik_mac=0, sari_kart=0, kirmizi_kart=0")
        conn.commit()
        conn.close()
        # Rebuild fixture
        self.fikstur_olustur(1, 1)
