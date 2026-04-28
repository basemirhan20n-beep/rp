# 🏛️ Parti Yönetim Simülasyonu + Cumhuriyet Süper Ligi

Telegram botu – parti yönetimi, görev, makam, güven puanı VE futbol ligi yönetimi.

## Yeni Özellikler
- **2. Lig**: 15 takım Süper Lig, 10 takım 1. Lig.
- **Kupa Sistemi**: Cumhuriyet Kupası (eleme usulü).
- **Sakatlık & Kart**: Oyuncular sakatlanır, kart cezası alır.
- **Taktik Seçimi**: 4-4-2, 4-3-3 vb. rakibe göre avantaj.
- **Genç Oyuncu**: Altyapıdan düşük maliyetli oyuncu.
- **Gol/Asist İstatistikleri**: Oyuncu bazlı.
- **Günlük Çark**: Para, XP veya özel ödül.
- **Bahis Sistemi** (altyapı hazır).
- **Lonca/Hizip**: Grup kurabilir, puan toplar.
- **Başarı Rozetleri** (achievement).
- **Admin Paneli**: Web dashboard (Flask, port 5000).
- **Grup Desteği**: `/set_group` ile maç sonuçları gruba gelir.
- **Transfer Dönemi**: Belirli aralıklarla piyasa açık/kapalı.
- **Sezon Sıfırlama**: `/sezon_sifirla` puanları sıfırlar, şampiyona ödül verir.

## Kurulum
```bash
pip install -r requirements.txt
# config.py içine BOT_TOKEN ve ADMIN_IDS gir
python bot.py
python web_dashboard.py
