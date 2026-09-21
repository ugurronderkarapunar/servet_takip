"""
database.py
SQLite tabanlı veri katmanı. Tüm yatırım işlemleri ve harcamalar
proje klasöründeki servet.db dosyasında saklanır (GitHub'a atarken
.gitignore ile hariç tutulur, böylece kendi verin özel kalır).
"""

import sqlite3
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent / "servet.db"

VARLIK_TURLERI = [
    "Dolar (USD)",
    "Euro (EUR)",
    "Altın (Gram)",
    "Altın (Çeyrek)",
    "Vadeli Mevduat (TL)",
    "Vadeli Mevduat (Döviz)",
    "Hisse Senedi",
    "Fon",
    "Diğer",
]

HARCAMA_KATEGORILERI = [
    "Yemek",
    "Market",
    "Fatura",
    "Kira",
    "Ulaşım",
    "Sağlık",
    "Giyim",
    "Eğlence",
    "Eğitim",
    "Diğer",
]


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS yatirimlar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT NOT NULL,
            varlik_turu TEXT NOT NULL,
            miktar REAL NOT NULL,
            birim_fiyat REAL NOT NULL,
            toplam_tutar REAL NOT NULL,
            vade_tarihi TEXT,
            faiz_orani REAL,
            not_alani TEXT,
            olusturma_zamani TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS harcamalar (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarih TEXT NOT NULL,
            kategori TEXT NOT NULL,
            tutar REAL NOT NULL,
            aciklama TEXT,
            olusturma_zamani TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS guncel_fiyatlar (
            varlik_turu TEXT PRIMARY KEY,
            fiyat REAL NOT NULL,
            guncelleme_zamani TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------- Yatırım işlemleri ----------

def yatirim_ekle(tarih, varlik_turu, miktar, birim_fiyat, vade_tarihi=None,
                  faiz_orani=None, not_alani=None):
    toplam_tutar = miktar * birim_fiyat
    conn = get_connection()
    conn.execute("""
        INSERT INTO yatirimlar
        (tarih, varlik_turu, miktar, birim_fiyat, toplam_tutar,
         vade_tarihi, faiz_orani, not_alani, olusturma_zamani)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (tarih, varlik_turu, miktar, birim_fiyat, toplam_tutar,
          vade_tarihi, faiz_orani, not_alani, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def yatirim_sil(yatirim_id):
    conn = get_connection()
    conn.execute("DELETE FROM yatirimlar WHERE id = ?", (yatirim_id,))
    conn.commit()
    conn.close()


def yatirimlari_getir():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM yatirimlar ORDER BY tarih DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Harcama işlemleri ----------

def harcama_ekle(tarih, kategori, tutar, aciklama=None):
    conn = get_connection()
    conn.execute("""
        INSERT INTO harcamalar (tarih, kategori, tutar, aciklama, olusturma_zamani)
        VALUES (?, ?, ?, ?, ?)
    """, (tarih, kategori, tutar, aciklama, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def harcama_sil(harcama_id):
    conn = get_connection()
    conn.execute("DELETE FROM harcamalar WHERE id = ?", (harcama_id,))
    conn.commit()
    conn.close()


def harcamalari_getir():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM harcamalar ORDER BY tarih DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------- Güncel fiyatlar (manuel veya otomatik çekilen) ----------

def guncel_fiyat_kaydet(varlik_turu, fiyat):
    conn = get_connection()
    conn.execute("""
        INSERT INTO guncel_fiyatlar (varlik_turu, fiyat, guncelleme_zamani)
        VALUES (?, ?, ?)
        ON CONFLICT(varlik_turu) DO UPDATE SET
            fiyat = excluded.fiyat,
            guncelleme_zamani = excluded.guncelleme_zamani
    """, (varlik_turu, fiyat, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def guncel_fiyatlari_getir():
    conn = get_connection()
    rows = conn.execute("SELECT * FROM guncel_fiyatlar").fetchall()
    conn.close()
    return {r["varlik_turu"]: dict(r) for r in rows}
