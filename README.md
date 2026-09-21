# 💰 Servet Takip

Kendi bilgisayarında (local) çalışan, kişisel yatırım ve harcamalarını
takip etmeni sağlayan basit bir Streamlit uygulaması. Verilerin sadece
kendi makinende, `servet.db` (SQLite) dosyasında saklanır — hiçbir yere
gönderilmez. `.gitignore` bu dosyayı GitHub'a yüklemeyecek şekilde
ayarlanmıştır, yani kodu paylaşabilir ama verini gizli tutabilirsin.

## Özellikler

- **Yatırım takibi**: Dolar, Euro, Altın (gram/çeyrek), Vadeli Mevduat,
  Hisse, Fon vb. — hangi kurdan/fiyattan ne kadar aldığını kaydet.
- **Vadeli mevduat için otomatik getiri hesabı**: Faiz oranı ve vade
  tarihini girdiğinde, bugüne kadar biriken tahmini getiriyi gösterir.
- **Harcama takibi**: Yemek, Fatura, Market, Kira, Ulaşım vb.
  kategorilere göre günlük harcama girişi.
- **Panel (Dashboard)**: Toplam yatırım maliyeti vs. güncel değer,
  kâr/zarar, toplam harcama, net servet, yatırım dağılım grafiği,
  harcama kategorisi grafiği, aylık harcama trend grafiği.
- **Güncel fiyat girişi**: Dolar/Euro/Altın için manuel fiyat girebilir
  ya da (internet varsa) tek tuşla otomatik çekebilirsin.
- **Kayıt yönetimi**: Girdiğin tüm kayıtları görüntüle, hatalı olanı
  ID'sinden sil.

## Kurulum

```bash
git clone <bu-repo-linki>
cd servet-takip
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Çalıştırma

```bash
streamlit run app.py
```

Tarayıcıda otomatik olarak `http://localhost:8501` açılır.

## Kullanım Örneği

> "15 Eylül'de 38,50 TL'den 500 dolar aldım" → **Yatırım Ekle**
> sayfasında Varlık Türü: Dolar (USD), Miktar: 500, Birim Fiyat: 38.50

> "Bugün yemeğe 250 TL, faturaya 800 TL harcadım" → **Harcama Ekle**
> sayfasında iki ayrı kayıt: Kategori Yemek / 250 ₺, Kategori Fatura / 800 ₺

## Klasör Yapısı

```
servet-takip/
├── app.py              # Ana Streamlit uygulaması (sayfalar burada)
├── database.py         # SQLite okuma/yazma fonksiyonları
├── fiyat_servisi.py     # Opsiyonel canlı kur/altın fiyatı çekme
├── requirements.txt
├── .gitignore           # servet.db GitHub'a gitmez
└── .streamlit/config.toml
```

## Notlar

- Altın fiyatı hesaplaması ons altın (USD) üzerinden yaklaşık olarak
  yapılır; kuyumcu/banka fiyatından küçük farklar olabilir.
- İnternet olmasa da uygulama tamamen çalışır — sadece güncel değer
  hesaplaması için fiyatları elle girmen gerekir.
- Kod tamamen senin, istediğin gibi kategori/varlık türü ekleyip
  değiştirebilirsin (`database.py` içindeki `VARLIK_TURLERI` ve
  `HARCAMA_KATEGORILERI` listeleri).
