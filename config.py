import os

# .env dosyasından veya ortam değişkenlerinden yükle
BOT_TOKEN = os.getenv("BOT_TOKEN", "BURAYA_BOT_TOKEN_YAZIN")

# Telegram user ID listesi — bu kişiler Parti Başkanı yetkisine sahip olur
# Örnek: ADMIN_IDS = [123456789, 987654321]
ADMIN_IDS: list[int] = []
