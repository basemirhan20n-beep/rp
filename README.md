# 🏛️ Parti Yönetim Simülasyonu — Telegram Botu

Telegram üzerinde çalışan, rol yapma (roleplay) tabanlı profesyonel parti yönetim simülasyon botu.

---

## 🚀 Kurulum

### 1. Gereksinimler

- Python 3.10+
- pip

### 2. Bağımlılıkları Yükle

```bash
pip install -r requirements.txt
```

### 3. Bot Token Ayarla

`config.py` dosyasını açın ve şu satırı düzenleyin:

```python
BOT_TOKEN = "BURAYA_BOT_TOKEN_YAZIN"
```

**Veya** ortam değişkeni olarak ayarlayın:

```bash
export BOT_TOKEN="telegram_bot_tokeniniz"
```

Bot token almak için Telegram'da [@BotFather](https://t.me/BotFather) ile konuşun.

### 4. Admin (Parti Başkanı) Yetkisi

`config.py` içindeki `ADMIN_IDS` listesine kendi Telegram kullanıcı ID'nizi ekleyin:

```python
ADMIN_IDS = [123456789]
```

Telegram ID'nizi öğrenmek için [@userinfobot](https://t.me/userinfobot) kullanabilirsiniz.

### 5. Botu Başlat

```bash
python bot.py
```

---

## 📋 Komutlar

### Genel Komutlar

| Komut | Açıklama |
|-------|----------|
| `/start` | Botu başlat, ana menüyü gör |
| `/profil` | Profil bilgilerini görüntüle |
| `/makam` | Makam durumunu kontrol et |
| `/gorev` | Günlük görev al |
| `/liderler` | Lider tablosunu görüntüle |

### Parti Başkanı Komutları

| Komut | Açıklama |
|-------|----------|
| `/rol_ver @kullanıcı Makam Adı` | Kullanıcıya makam ata |
| `/rol_al @kullanıcı` | Kullanıcının makamını al |
| `/duyuru Mesaj` | Tüm üyelere duyuru gönder |
| `/puan_ver @kullanıcı miktar` | Kullanıcıya XP ver |
| `/guven_ver @kullanıcı miktar` | Kullanıcının güven puanını değiştir |

---

## 🏛️ Makamlar

- Parti Başkanı
- Genel Sekreter
- Ekonomi Başkanı
- Eğitim Başkanı
- Kooperatif Sorumlusu
- İçişleri Sorumlusu
- Parti Yöneticisi

---

## 📊 Sistem Kuralları

### XP & Seviye
- Görev tamamlama: **+20 XP** + Seri bonusu (Seri × 5 XP)
- 10 seviye bulunmaktadır

### Güven Puanı
| Durum | Puan |
|-------|------|
| 🟢 Güvenli Koltuk | 75 – 100 |
| 🟡 Dikkatli | 50 – 74 |
| 🔴 Riskli | 30 – 49 |
| ⛔ Kritik | 0 – 29 |

- Görev yapmazsan: **-5 güven/gün**
- Görev yaparsan: **+3 güven**
- 30 altı: Görevden alma uyarısı

### Seri (Streak)
- Her günlük görev: +1
- Kaçırınca: 0'a sıfırlanır
- Seri bonusu: Seri × 5 XP

---

## 📁 Dosya Yapısı

```
parti_botu/
├── bot.py          # Ana bot dosyası
├── database.py     # SQLite veritabanı işlemleri
├── config.py       # Token ve admin ayarları
├── requirements.txt
└── README.md
```

---

## 🗃️ Veritabanı

Bot çalıştırıldığında otomatik olarak `parti.db` dosyası oluşturulur. Yedeklemek için bu dosyayı kopyalamanız yeterlidir.
