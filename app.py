"""
Kişisel Servet Yönetim Uygulaması
----------------------------------
Yerel (local) çalışan, verisi SQLite'ta senin bilgisayarında kalan
basit bir servet/harcama takip aracı.

Çalıştırmak için:
    pip install -r requirements.txt
    streamlit run app.py
"""

from datetime import date, datetime

import pandas as pd
import plotly.express as px
import streamlit as st

import database as db
import fiyat_servisi

st.set_page_config(
    page_title="Servet Takip",
    page_icon="💰",
    layout="wide",
)

db.init_db()


# ----------------------------------------------------------------------
# Yardımcı fonksiyonlar
# ----------------------------------------------------------------------

def tl_formatla(sayi):
    try:
        return f"{sayi:,.2f} ₺".replace(",", "X").replace(".", ",").replace("X", ".")
    except Exception:
        return str(sayi)


def yatirim_guncel_deger(satir, guncel_fiyatlar):
    """
    Bir yatırım satırının bugünkü tahmini değerini hesaplar.
    Güncel fiyat girilmemişse, alım fiyatı üzerinden hesaplanır
    (yani kâr/zarar 0 gösterilir).
    """
    tur = satir["varlik_turu"]
    guncel = guncel_fiyatlar.get(tur, {}).get("fiyat")
    if tur.startswith("Vadeli Mevduat"):
        # Vadeli mevduat için faiz oranına göre basit getiri hesapla
        if satir.get("faiz_orani") and satir.get("vade_tarihi"):
            try:
                baslangic = datetime.strptime(satir["tarih"], "%Y-%m-%d").date()
                vade = datetime.strptime(satir["vade_tarihi"], "%Y-%m-%d").date()
                gun_sayisi = max((vade - baslangic).days, 0)
                yillik_faiz = satir["faiz_orani"] / 100
                getiri = satir["toplam_tutar"] * yillik_faiz * (gun_sayisi / 365)
                bugun = date.today()
                if bugun >= vade:
                    return satir["toplam_tutar"] + getiri
                else:
                    gecen_gun = max((bugun - baslangic).days, 0)
                    kismi_getiri = satir["toplam_tutar"] * yillik_faiz * (gecen_gun / 365)
                    return satir["toplam_tutar"] + kismi_getiri
            except Exception:
                return satir["toplam_tutar"]
        return satir["toplam_tutar"]
    if guncel:
        return satir["miktar"] * guncel
    return satir["toplam_tutar"]


# ----------------------------------------------------------------------
# Kenar çubuğu (sayfa seçimi)
# ----------------------------------------------------------------------

st.sidebar.title("💰 Servet Takip")
sayfa = st.sidebar.radio(
    "Sayfa seç",
    ["📊 Panel (Dashboard)", "📈 Yatırım Ekle", "🧾 Harcama Ekle", "⚙️ Güncel Fiyatlar", "🗂️ Kayıtlar"],
)

st.sidebar.markdown("---")
st.sidebar.caption("Tüm verilerin `servet.db` dosyasında, sadece kendi bilgisayarında saklanır.")


# ----------------------------------------------------------------------
# 1) PANEL / DASHBOARD
# ----------------------------------------------------------------------

if sayfa == "📊 Panel (Dashboard)":
    st.title("📊 Genel Durum")

    yatirimlar = db.yatirimlari_getir()
    harcamalar = db.harcamalari_getir()
    guncel_fiyatlar = db.guncel_fiyatlari_getir()

    if not yatirimlar and not harcamalar:
        st.info("Henüz veri yok. Soldaki menüden 'Yatırım Ekle' veya 'Harcama Ekle' ile başlayabilirsin.")
    else:
        df_yatirim = pd.DataFrame(yatirimlar)
        df_harcama = pd.DataFrame(harcamalar)

        toplam_yatirim_maliyet = df_yatirim["toplam_tutar"].sum() if not df_yatirim.empty else 0
        toplam_yatirim_guncel = 0
        if not df_yatirim.empty:
            df_yatirim["guncel_deger"] = df_yatirim.apply(
                lambda r: yatirim_guncel_deger(r, guncel_fiyatlar), axis=1
            )
            toplam_yatirim_guncel = df_yatirim["guncel_deger"].sum()

        toplam_harcama = df_harcama["tutar"].sum() if not df_harcama.empty else 0
        kar_zarar = toplam_yatirim_guncel - toplam_yatirim_maliyet

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Toplam Yatırım (Maliyet)", tl_formatla(toplam_yatirim_maliyet))
        col2.metric("Güncel Yatırım Değeri", tl_formatla(toplam_yatirim_guncel),
                     delta=tl_formatla(kar_zarar))
        col3.metric("Toplam Harcama", tl_formatla(toplam_harcama))
        col4.metric("Net Servet (tahmini)", tl_formatla(toplam_yatirim_guncel - toplam_harcama))

        st.markdown("---")

        c1, c2 = st.columns(2)

        with c1:
            st.subheader("Yatırım Dağılımı")
            if not df_yatirim.empty:
                dagilim = df_yatirim.groupby("varlik_turu")["guncel_deger"].sum().reset_index()
                fig = px.pie(dagilim, names="varlik_turu", values="guncel_deger", hole=0.4)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.caption("Henüz yatırım kaydı yok.")

        with c2:
            st.subheader("Harcama Kategorileri")
            if not df_harcama.empty:
                kat_dagilim = df_harcama.groupby("kategori")["tutar"].sum().reset_index()
                fig2 = px.pie(kat_dagilim, names="kategori", values="tutar", hole=0.4)
                st.plotly_chart(fig2, use_container_width=True)
            else:
                st.caption("Henüz harcama kaydı yok.")

        st.markdown("---")
        st.subheader("Aylık Harcama Trendi")
        if not df_harcama.empty:
            df_harcama["tarih_dt"] = pd.to_datetime(df_harcama["tarih"])
            df_harcama["ay"] = df_harcama["tarih_dt"].dt.to_period("M").astype(str)
            aylik = df_harcama.groupby("ay")["tutar"].sum().reset_index()
            fig3 = px.bar(aylik, x="ay", y="tutar", labels={"ay": "Ay", "tutar": "Toplam Harcama (₺)"})
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.caption("Henüz harcama kaydı yok.")


# ----------------------------------------------------------------------
# 2) YATIRIM EKLE
# ----------------------------------------------------------------------

elif sayfa == "📈 Yatırım Ekle":
    st.title("📈 Yeni Yatırım İşlemi")
    st.caption("Örnek: 15.09.2026 tarihinde 38,50 ₺'den 500 dolar aldım gibi.")

    with st.form("yatirim_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tarih = st.date_input("İşlem Tarihi", value=date.today())
            varlik_turu = st.selectbox("Varlık Türü", db.VARLIK_TURLERI)
            miktar = st.number_input("Miktar (adet / gram / dolar tutarı)", min_value=0.0, step=0.01, format="%.4f")
        with col2:
            birim_fiyat = st.number_input("Birim Fiyat / Kur (₺)", min_value=0.0, step=0.01, format="%.4f")
            vade_tarihi = None
            faiz_orani = None
            if varlik_turu.startswith("Vadeli Mevduat"):
                vade_tarihi = st.date_input("Vade Tarihi", value=date.today())
                faiz_orani = st.number_input("Yıllık Faiz Oranı (%)", min_value=0.0, step=0.1)
            not_alani = st.text_input("Not (banka, kuyumcu, aracı kurum vb. - opsiyonel)")

        toplam = miktar * birim_fiyat
        st.markdown(f"**Toplam Tutar: {tl_formatla(toplam)}**")

        gonder = st.form_submit_button("Kaydet")
        if gonder:
            if miktar <= 0 or birim_fiyat <= 0:
                st.error("Miktar ve birim fiyat sıfırdan büyük olmalı.")
            else:
                db.yatirim_ekle(
                    tarih=tarih.isoformat(),
                    varlik_turu=varlik_turu,
                    miktar=miktar,
                    birim_fiyat=birim_fiyat,
                    vade_tarihi=vade_tarihi.isoformat() if vade_tarihi else None,
                    faiz_orani=faiz_orani,
                    not_alani=not_alani or None,
                )
                st.success("Yatırım kaydedildi ✅")


# ----------------------------------------------------------------------
# 3) HARCAMA EKLE
# ----------------------------------------------------------------------

elif sayfa == "🧾 Harcama Ekle":
    st.title("🧾 Yeni Harcama")
    st.caption("Örnek: bugün yemeğe 250 ₺, faturaya 800 ₺ harcadım gibi, her birini ayrı ayrı gir.")

    with st.form("harcama_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            tarih = st.date_input("Harcama Tarihi", value=date.today())
            kategori = st.selectbox("Kategori", db.HARCAMA_KATEGORILERI)
        with col2:
            tutar = st.number_input("Tutar (₺)", min_value=0.0, step=0.01, format="%.2f")
            aciklama = st.text_input("Açıklama (opsiyonel)")

        gonder = st.form_submit_button("Kaydet")
        if gonder:
            if tutar <= 0:
                st.error("Tutar sıfırdan büyük olmalı.")
            else:
                db.harcama_ekle(
                    tarih=tarih.isoformat(),
                    kategori=kategori,
                    tutar=tutar,
                    aciklama=aciklama or None,
                )
                st.success("Harcama kaydedildi ✅")


# ----------------------------------------------------------------------
# 4) GÜNCEL FİYATLAR
# ----------------------------------------------------------------------

elif sayfa == "⚙️ Güncel Fiyatlar":
    st.title("⚙️ Güncel Fiyatları Ayarla")
    st.caption(
        "Portföyünün bugünkü değerini hesaplayabilmek için dolar/euro/altın "
        "fiyatlarını gir. İnternet bağlantın varsa otomatik çekmeyi deneyebilirsin."
    )

    if st.button("🌐 İnternetten Otomatik Çek"):
        with st.spinner("Fiyatlar çekiliyor..."):
            sonuclar = fiyat_servisi.tum_fiyatlari_cek()
        basarili = 0
        for tur, fiyat in sonuclar.items():
            if fiyat is not None:
                db.guncel_fiyat_kaydet(tur, fiyat)
                basarili += 1
        if basarili:
            st.success(f"{basarili} fiyat başarıyla güncellendi.")
        else:
            st.warning("Otomatik çekme başarısız oldu (internet yok olabilir). Aşağıdan manuel girebilirsin.")

    st.markdown("---")
    st.subheader("Manuel Fiyat Girişi")

    guncel = db.guncel_fiyatlari_getir()

    with st.form("fiyat_form"):
        fiyat_girisleri = {}
        for tur in db.VARLIK_TURLERI:
            if tur.startswith("Vadeli Mevduat"):
                continue  # vadeli mevduat faize göre hesaplanıyor, güncel fiyat gerekmez
            mevcut = guncel.get(tur, {}).get("fiyat", 0.0)
            fiyat_girisleri[tur] = st.number_input(
                f"{tur} - Güncel Birim Fiyat (₺)", min_value=0.0, value=float(mevcut), step=0.01, format="%.4f"
            )
        gonder = st.form_submit_button("Fiyatları Kaydet")
        if gonder:
            for tur, fiyat in fiyat_girisleri.items():
                if fiyat > 0:
                    db.guncel_fiyat_kaydet(tur, fiyat)
            st.success("Fiyatlar kaydedildi ✅")

    if guncel:
        st.markdown("---")
        st.caption("Son güncelleme zamanları:")
        for tur, bilgi in guncel.items():
            st.text(f"{tur}: {bilgi['fiyat']} ₺  —  {bilgi['guncelleme_zamani'][:19]}")


# ----------------------------------------------------------------------
# 5) KAYITLAR (listeleme / silme)
# ----------------------------------------------------------------------

elif sayfa == "🗂️ Kayıtlar":
    st.title("🗂️ Tüm Kayıtlar")

    tab1, tab2 = st.tabs(["Yatırımlar", "Harcamalar"])

    with tab1:
        yatirimlar = db.yatirimlari_getir()
        if yatirimlar:
            df = pd.DataFrame(yatirimlar)
            st.dataframe(df, use_container_width=True, hide_index=True)
            silinecek = st.number_input("Silinecek kaydın ID'si", min_value=0, step=1, key="sil_yatirim")
            if st.button("Yatırım Kaydını Sil"):
                if silinecek > 0:
                    db.yatirim_sil(int(silinecek))
                    st.success("Silindi, sayfayı yenile.")
        else:
            st.caption("Henüz yatırım kaydı yok.")

    with tab2:
        harcamalar = db.harcamalari_getir()
        if harcamalar:
            df = pd.DataFrame(harcamalar)
            st.dataframe(df, use_container_width=True, hide_index=True)
            silinecek = st.number_input("Silinecek kaydın ID'si", min_value=0, step=1, key="sil_harcama")
            if st.button("Harcama Kaydını Sil"):
                if silinecek > 0:
                    db.harcama_sil(int(silinecek))
                    st.success("Silindi, sayfayı yenile.")
        else:
            st.caption("Henüz harcama kaydı yok.")
