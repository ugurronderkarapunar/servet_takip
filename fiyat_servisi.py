"""
fiyat_servisi.py
İnternet bağlantısı varsa güncel Dolar/Euro/Altın (TL) fiyatlarını
ücretsiz bir kaynaktan çekmeye çalışır. Bağlantı yoksa ya da kaynak
cevap vermezse None döner; uygulama bu durumda kullanıcıdan manuel
fiyat girmesini ister. Böylece uygulama internetsiz de çalışır.
"""

import requests

TIMEOUT = 5


def usd_try_kuru():
    try:
        r = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD", timeout=TIMEOUT
        )
        r.raise_for_status()
        return round(r.json()["rates"]["TRY"], 4)
    except Exception:
        return None


def eur_try_kuru():
    try:
        r = requests.get(
            "https://api.exchangerate-api.com/v4/latest/EUR", timeout=TIMEOUT
        )
        r.raise_for_status()
        return round(r.json()["rates"]["TRY"], 4)
    except Exception:
        return None


def gram_altin_tl():
    """
    Gram altın TL fiyatını, ons altın (USD) x USD/TRY kurundan yaklaşık
    olarak hesaplar (1 ons = 31.1035 gram). Kesin banka/kuyumcu fiyatından
    küçük farklar olabilir; sadece takip amaçlıdır.
    """
    try:
        usd_try = usd_try_kuru()
        if usd_try is None:
            return None
        r = requests.get(
            "https://api.metals.live/v1/spot/gold", timeout=TIMEOUT
        )
        r.raise_for_status()
        data = r.json()
        ons_usd = data[0]["price"] if isinstance(data, list) else data["price"]
        gram_usd = ons_usd / 31.1035
        return round(gram_usd * usd_try, 2)
    except Exception:
        return None


def tum_fiyatlari_cek():
    """Dict olarak sonuç döner; çekilemeyenler None olur."""
    return {
        "Dolar (USD)": usd_try_kuru(),
        "Euro (EUR)": eur_try_kuru(),
        "Altın (Gram)": gram_altin_tl(),
    }
