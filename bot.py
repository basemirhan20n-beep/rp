import logging
import random
import asyncio
from datetime import datetime, date, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    ContextTypes, MessageHandler, filters
)
from database import Database
from config import BOT_TOKEN, ADMIN_IDS

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

db = Database()

MAKAMLAR = [
    "Parti Başkanı",
    "Genel Sekreter",
    "Ekonomi Başkanı",
    "Eğitim Başkanı",
    "Kooperatif Sorumlusu",
    "İçişleri Sorumlusu",
    "Parti Yöneticisi",
]

GOREVLER = {
    "Parti Başkanı": [
        "Parti genel kararını açıkla ve üyeleri bilgilendir.",
        "Kritik bir krizi çöz ve strateji belirle.",
        "Yeni parti stratejisi belirle ve duyur.",
        "Yönetim kurulunu topla ve kararları kayıt altına al.",
        "Dış ilişkileri değerlendir ve rapor hazırla.",
    ],
    "Genel Sekreter": [
        "Parti içi düzen raporu hazırla ve sun.",
        "Tüm üyelerin durumunu kontrol et ve belgele.",
        "Bu haftaki toplantıyı organize et ve davetleri gönder.",
        "Arşivleri güncelle ve eksik belgeleri tamamla.",
        "Parti yazışmalarını düzenle ve cevapla.",
    ],
    "Ekonomi Başkanı": [
        "Aylık bütçe planı hazırla ve onayla.",
        "Gelir-gider raporu yaz ve sunuma hazırla.",
        "Ekonomik öneri paketi oluştur ve yönetime ilet.",
        "Harcamaları denetle ve tasarruf önerileri sun.",
        "Gelecek çeyrek için mali projeksiyon hazırla.",
    ],
    "Eğitim Başkanı": [
        "Parti üyeleri için eğitim planı oluştur.",
        "Üyelere kişisel gelişim önerileri sun.",
        "Eğitim duyurusunu hazırla ve dağıt.",
        "Eğitim materyallerini güncelle ve arşivle.",
        "Eğitim etkinliği sonuç raporu hazırla.",
    ],
    "Kooperatif Sorumlusu": [
        "Bu dönem için üretim planı hazırla.",
        "Kooperatif faaliyet raporu yaz ve sun.",
        "Gelir artırma önerisi geliştir ve belgele.",
        "Kooperatif üyelerini denetle ve raporla.",
        "Yeni ortaklık fırsatlarını araştır ve sun.",
    ],
    "İçişleri Sorumlusu": [
        "Parti içi güvenlik denetimi gerçekleştir.",
        "Sorunlu durumları tespit et ve raporla.",
        "Disiplin raporu hazırla ve yönetime sun.",
        "Üye şikayetlerini incele ve çözüme kavuştur.",
        "İç denetim çalışması yap ve belgele.",
    ],
    "Parti Yöneticisi": [
        "Üyelere operasyonel destek ver ve takibini yap.",
        "Parti içi süreç iyileştirme önerisi sun.",
        "Üyeler arası iletişimi artıracak plan hazırla.",
        "Haftalık yönetim özeti hazırla ve dağıt.",
        "Yeni üye oryantasyon programı organize et.",
    ],
}

GOREV_MESAJLARI = {
    "Parti Başkanı": [
        "🏛️ Parti Başkanı genel kararını açıkladı, parti yönü netleşti.",
        "🏛️ Başkan krizi ustaca yönetti, parti istikrarı korundu.",
        "🏛️ Yeni strateji Başkan tarafından belirlendi, harekete geçildi.",
    ],
    "Genel Sekreter": [
        "📋 Genel Sekreter düzen raporunu tamamladı, sistem sorunsuz işliyor.",
        "📋 Sekreter üye kontrolünü tamamladı, kayıtlar güncellendi.",
        "📋 Toplantı organizasyonu Sekreter tarafından sağlandı.",
    ],
    "Ekonomi Başkanı": [
        "💰 Ekonomi Başkanı bütçe planını açıkladı, mali denge sağlandı.",
        "💰 Gelir-gider raporu sunuldu, ekonomik tablo netleşti.",
        "💰 Yeni ekonomik öneri paketi yönetime iletildi.",
    ],
    "Eğitim Başkanı": [
        "📚 Eğitim Başkanı yeni eğitim planını devreye aldı.",
        "📚 Üyelere gelişim programı sunuldu, katılım sağlandı.",
        "📚 Eğitim duyurusu yapıldı, program başlatıldı.",
    ],
    "Kooperatif Sorumlusu": [
        "🌾 Kooperatif Sorumlusu üretim planını onayladı.",
        "🌾 Kooperatif raporu tamamlandı, verimlilik artırıldı.",
        "🌾 Gelir artırma önerisi hayata geçirildi.",
    ],
    "İçişleri Sorumlusu": [
        "🔒 İçişleri Sorumlusu güvenlik denetimini tamamladı.",
        "🔒 Sorunlar tespit edildi, disiplin prosedürü başlatıldı.",
        "🔒 Disiplin raporu hazırlandı, iç düzen sağlandı.",
    ],
    "Parti Yöneticisi": [
        "⚙️ Parti Yöneticisi üyelere gerekli desteği sağladı.",
        "⚙️ Süreç iyileştirme önerisi yönetimce kabul edildi.",
        "⚙️ İletişim kanalları güçlendirildi, koordinasyon arttı.",
    ],
}

SEVIYE_ESLEME = {
    1: 0, 2: 100, 3: 250, 4: 500, 5: 1000,
    6: 2000, 7: 3500, 8: 5500, 9: 8000, 10: 12000,
}


def seviye_hesapla(xp: int) -> int:
    seviye = 1
    for lvl, gerekli_xp in sorted(SEVIYE_ESLEME.items(), reverse=True):
        if xp >= gerekli_xp:
            seviye = lvl
            break
    return seviye


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    klavye = [
        [
            InlineKeyboardButton("📌 Görev Yap", callback_data="gorev_yap"),
            InlineKeyboardButton("👤 Profil", callback_data="profil"),
        ],
        [
            InlineKeyboardButton("🏛️ Makam Kontrol", callback_data="makam"),
            InlineKeyboardButton("🏆 Liderler", callback_data="liderler"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(klavye)
    await update.message.reply_text(
        f"🏛️ *Parti Yönetim Sistemi'ne Hoş Geldiniz*\n\n"
        f"Sayın {user.first_name}, partimizin güçlü bir üyesi olarak görevinizi yerine getirmekle yükümlüsünüz.\n\n"
        f"Günlük görevinizi yaparak XP ve güven kazanın. Görevlerinizi ihmal etmek koltuğunuzu tehlikeye atar.\n\n"
        f"_Parti her şeyden önce gelir._",
        parse_mode="Markdown",
        reply_markup=reply_markup,
    )


async def profil_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    veri = db.kullanici_getir(user.id)
    await _profil_goster(update, veri, user.first_name)


async def _profil_goster(update, veri, isim):
    xp = veri["xp"]
    level = seviye_hesapla(xp)
    guven = veri["guven"]
    streak = veri["streak"]
    rol = veri["role"] or "Atanmamış"

    if guven >= 75:
        durum = "🟢 Güvenli"
    elif guven >= 50:
        durum = "🟡 Dikkatli"
    elif guven >= 30:
        durum = "🟠 Riskli"
    else:
        durum = "🔴 Kritik"

    sonraki_seviye = SEVIYE_ESLEME.get(level + 1, None)
    if sonraki_seviye:
        kalan_xp = sonraki_seviye - xp
        xp_bilgi = f"{xp} XP (Sonraki seviye için {kalan_xp} XP)"
    else:
        xp_bilgi = f"{xp} XP (Maksimum seviye)"

    mesaj = (
        f"👤 *{isim} — Profil*\n"
        f"{'─' * 28}\n"
        f"🏛️ *Makam:* {rol}\n"
        f"⭐ *Seviye:* {level}\n"
        f"🔷 *XP:* {xp_bilgi}\n"
        f"🛡️ *Güven:* {guven}/100 — {durum}\n"
        f"🔥 *Seri:* {streak} gün\n"
    )
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown")


async def makam_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    veri = db.kullanici_getir(user.id)
    rol = veri["role"]
    guven = veri["guven"]

    if not rol:
        mesaj = (
            "🏛️ *Makam Durumu*\n"
            "─────────────────────\n"
            "⚠️ Henüz bir makama atanmadınız.\n"
            "Parti Başkanı sizin için bir görev belirleyene kadar beklemeniz gerekmektedir."
        )
    else:
        if guven >= 75:
            durum = "🟢 Güvenli Koltuk"
        elif guven >= 50:
            durum = "🟡 Dikkat Gerektiren Koltuk"
        elif guven >= 30:
            durum = "🔴 Riskli Koltuk"
        else:
            durum = "⛔ Kritik — Görevden Alma Süreci"

        mesaj = (
            f"🏛️ *Makam Durumu*\n"
            f"─────────────────────\n"
            f"📌 *Makam:* {rol}\n"
            f"🛡️ *Güven Puanı:* {guven}/100\n"
            f"📊 *Durum:* {durum}\n"
        )
        if guven < 50:
            mesaj += "\n⚠️ _Güven puanınız tehlikeli düzeyde. Görevlerinizi aksatmayın!_"
        if guven < 30:
            mesaj += "\n🚨 _Görevden alma oylaması başlatılabilir!_"

    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown")


async def gorev_yap_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    veri = db.kullanici_getir(user.id)
    rol = veri["role"]

    if not rol:
        mesaj = "⚠️ Henüz bir makama atanmadınız. Görev yapamazsınız."
        if hasattr(update, "message") and update.message:
            await update.message.reply_text(mesaj)
        else:
            await update.callback_query.edit_message_text(mesaj)
        return

    bugun = date.today().isoformat()
    if veri["last_task"] == bugun:
        mesaj = "✅ Bugünkü görevinizi zaten tamamladınız. Yarın tekrar gelin."
        if hasattr(update, "message") and update.message:
            await update.message.reply_text(mesaj)
        else:
            await update.callback_query.edit_message_text(mesaj)
        return

    gorev = random.choice(GOREVLER[rol])
    klavye = [
        [
            InlineKeyboardButton("✅ Görevi Tamamladım", callback_data=f"gorev_tamamla"),
        ]
    ]
    reply_markup = InlineKeyboardMarkup(klavye)
    mesaj = (
        f"📌 *Günlük Göreviniz*\n"
        f"─────────────────────\n"
        f"🏛️ *Makam:* {rol}\n\n"
        f"📋 *Görev:*\n_{gorev}_\n\n"
        f"Görevi tamamladıktan sonra butona basın."
    )
    context.user_data["aktif_gorev"] = gorev
    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown", reply_markup=reply_markup)


async def gorev_tamamla(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = update.effective_user
    veri = db.kullanici_getir(user.id)

    if not veri:
        await query.edit_message_text("Kayıt bulunamadı. /start ile başlayın.")
        return

    bugun = date.today().isoformat()
    if veri["last_task"] == bugun:
        await query.edit_message_text("✅ Bu görevi zaten tamamladınız.")
        return

    rol = veri["role"]
    if not rol:
        await query.edit_message_text("⚠️ Makamınız bulunmamaktadır.")
        return

    streak = veri["streak"] + 1
    bonus_xp = streak * 5
    kazanilan_xp = 20 + bonus_xp
    yeni_xp = veri["xp"] + kazanilan_xp
    yeni_guven = min(100, veri["guven"] + 3)
    yeni_level = seviye_hesapla(yeni_xp)
    eski_level = seviye_hesapla(veri["xp"])

    db.kullanici_guncelle(
        user_id=user.id,
        xp=yeni_xp,
        level=yeni_level,
        guven=yeni_guven,
        streak=streak,
        last_task=bugun,
    )

    mesaj_metni = random.choice(GOREV_MESAJLARI[rol])
    seviye_mesaji = ""
    if yeni_level > eski_level:
        seviye_mesaji = f"\n\n🎉 *SEVİYE ATLADI!* → Seviye {yeni_level}"

    mesaj = (
        f"✅ *Görev Tamamlandı*\n"
        f"─────────────────────\n"
        f"{mesaj_metni}\n\n"
        f"🔷 *Kazanılan XP:* +{kazanilan_xp} (Baz: 20 + Seri Bonusu: {bonus_xp})\n"
        f"🛡️ *Güven:* {yeni_guven}/100 (+3)\n"
        f"🔥 *Seri:* {streak} gün{seviye_mesaji}"
    )

    klavye = [
        [
            InlineKeyboardButton("👤 Profilim", callback_data="profil"),
            InlineKeyboardButton("🏛️ Makamım", callback_data="makam"),
        ]
    ]
    await query.edit_message_text(mesaj, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(klavye))


async def liderler_komutu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    liderler = db.lider_tablosu()
    if not liderler:
        mesaj = "📊 Henüz lider tablosunda kimse yok."
    else:
        satirlar = ["🏆 *Lider Tablosu — İlk 10*\n" + "─" * 28]
        madalyalar = ["🥇", "🥈", "🥉"]
        for i, (isim, xp, rol, guven) in enumerate(liderler):
            madalya = madalyalar[i] if i < 3 else f"{i + 1}."
            rol_kisa = rol or "Atanmamış"
            satirlar.append(f"{madalya} *{isim}* — {xp} XP | {rol_kisa} | Güven: {guven}")
        mesaj = "\n".join(satirlar)

    if hasattr(update, "message") and update.message:
        await update.message.reply_text(mesaj, parse_mode="Markdown")
    else:
        await update.callback_query.edit_message_text(mesaj, parse_mode="Markdown")


async def rol_ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.kullanici_ekle(user.id, user.username or user.first_name)
    veri = db.kullanici_getir(user.id)

    if veri["role"] != "Parti Başkanı" and user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Bu komutu yalnızca Parti Başkanı kullanabilir.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text(
            "⚠️ Kullanım: `/rol_ver @kullanıcıadı Makam Adı`\n"
            "Örnek: `/rol_ver @ahmet Ekonomi Başkanı`",
            parse_mode="Markdown",
        )
        return

    hedef_username = args[0].lstrip("@")
    makam = " ".join(args[1:])

    if makam not in MAKAMLAR:
        makam_listesi = "\n".join([f"• {m}" for m in MAKAMLAR])
        await update.message.reply_text(
            f"⚠️ Geçersiz makam. Mevcut makamlar:\n{makam_listesi}"
        )
        return

    hedef = db.kullanici_username_ile_getir(hedef_username)
    if not hedef:
        await update.message.reply_text(f"⚠️ `{hedef_username}` kullanıcısı sistemde bulunamadı.")
        return

    db.rol_ata(hedef["user_id"], makam)
    await update.message.reply_text(
        f"✅ *{hedef_username}* kullanıcısına *{makam}* görevi verildi.",
        parse_mode="Markdown",
    )


async def rol_al(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    veri = db.kullanici_getir(user.id)

    if not veri or (veri["role"] != "Parti Başkanı" and user.id not in ADMIN_IDS):
        await update.message.reply_text("⛔ Bu komutu yalnızca Parti Başkanı kullanabilir.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Kullanım: `/rol_al @kullanıcıadı`", parse_mode="Markdown")
        return

    hedef_username = args[0].lstrip("@")
    hedef = db.kullanici_username_ile_getir(hedef_username)
    if not hedef:
        await update.message.reply_text(f"⚠️ `{hedef_username}` kullanıcısı bulunamadı.")
        return

    db.rol_ata(hedef["user_id"], None)
    await update.message.reply_text(
        f"✅ *{hedef_username}* kullanıcısının görevi alındı.",
        parse_mode="Markdown",
    )


async def duyuru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    veri = db.kullanici_getir(user.id)

    if not veri or (veri["role"] != "Parti Başkanı" and user.id not in ADMIN_IDS):
        await update.message.reply_text("⛔ Bu komutu yalnızca Parti Başkanı kullanabilir.")
        return

    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/duyuru Mesaj metni`", parse_mode="Markdown")
        return

    duyuru_metni = " ".join(context.args)
    tum_kullanicilar = db.tum_kullanicilari_getir()
    basarili = 0
    for uid, _ in tum_kullanicilar:
        try:
            await context.bot.send_message(
                chat_id=uid,
                text=f"📢 *PARTİ DUYURUSU*\n{'─' * 28}\n{duyuru_metni}",
                parse_mode="Markdown",
            )
            basarili += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Duyuru {basarili} üyeye iletildi.")


async def puan_ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    veri = db.kullanici_getir(user.id)

    if not veri or (veri["role"] != "Parti Başkanı" and user.id not in ADMIN_IDS):
        await update.message.reply_text("⛔ Bu komutu yalnızca Parti Başkanı kullanabilir.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Kullanım: `/puan_ver @kullanıcı miktar`", parse_mode="Markdown")
        return

    hedef_username = args[0].lstrip("@")
    try:
        miktar = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Miktar sayısal olmalıdır.")
        return

    hedef = db.kullanici_username_ile_getir(hedef_username)
    if not hedef:
        await update.message.reply_text(f"⚠️ `{hedef_username}` bulunamadı.")
        return

    yeni_xp = hedef["xp"] + miktar
    yeni_level = seviye_hesapla(yeni_xp)
    db.kullanici_guncelle(hedef["user_id"], xp=yeni_xp, level=yeni_level)
    await update.message.reply_text(
        f"✅ *{hedef_username}* kullanıcısına *{miktar} XP* verildi. Toplam: {yeni_xp} XP",
        parse_mode="Markdown",
    )


async def guven_ver(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    veri = db.kullanici_getir(user.id)

    if not veri or (veri["role"] != "Parti Başkanı" and user.id not in ADMIN_IDS):
        await update.message.reply_text("⛔ Bu komutu yalnızca Parti Başkanı kullanabilir.")
        return

    args = context.args
    if len(args) < 2:
        await update.message.reply_text("⚠️ Kullanım: `/guven_ver @kullanıcı miktar`", parse_mode="Markdown")
        return

    hedef_username = args[0].lstrip("@")
    try:
        miktar = int(args[1])
    except ValueError:
        await update.message.reply_text("⚠️ Miktar sayısal olmalıdır.")
        return

    hedef = db.kullanici_username_ile_getir(hedef_username)
    if not hedef:
        await update.message.reply_text(f"⚠️ `{hedef_username}` bulunamadı.")
        return

    yeni_guven = max(0, min(100, hedef["guven"] + miktar))
    db.kullanici_guncelle(hedef["user_id"], guven=yeni_guven)
    await update.message.reply_text(
        f"✅ *{hedef_username}* kullanıcısının güveni *{miktar}* değiştirildi. Yeni güven: {yeni_guven}",
        parse_mode="Markdown",
    )


async def buton_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "profil":
        user = update.effective_user
        db.kullanici_ekle(user.id, user.username or user.first_name)
        veri = db.kullanici_getir(user.id)
        await _profil_goster(update, veri, user.first_name)
    elif data == "makam":
        await makam_komutu(update, context)
    elif data == "gorev_yap":
        await gorev_yap_komutu(update, context)
    elif data == "gorev_tamamla":
        await gorev_tamamla(update, context)
    elif data == "liderler":
        await liderler_komutu(update, context)
    elif data == "ana_menu":
        klavye = [
            [
                InlineKeyboardButton("📌 Görev Yap", callback_data="gorev_yap"),
                InlineKeyboardButton("👤 Profil", callback_data="profil"),
            ],
            [
                InlineKeyboardButton("🏛️ Makam Kontrol", callback_data="makam"),
                InlineKeyboardButton("🏆 Liderler", callback_data="liderler"),
            ],
        ]
        await query.edit_message_text(
            "🏛️ *Ana Menü*\nAşağıdan bir seçenek belirleyin:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(klavye),
        )


async def gunluk_ceza_isle(context: ContextTypes.DEFAULT_TYPE):
    tum = db.tum_kullanicilari_getir()
    bugun = date.today().isoformat()
    dun = (date.today() - timedelta(days=1)).isoformat()

    for user_id, _ in tum:
        veri = db.kullanici_getir(user_id)
        if not veri or not veri["role"]:
            continue
        if veri["last_task"] in (bugun, None):
            continue
        if veri["last_task"] == dun:
            continue

        son_gorev = veri["last_task"]
        if son_gorev:
            try:
                son_tarih = date.fromisoformat(son_gorev)
                fark = (date.today() - son_tarih).days
            except Exception:
                fark = 1
        else:
            fark = 1

        ceza = min(5 * fark, 30)
        yeni_guven = max(0, veri["guven"] - ceza)
        db.kullanici_guncelle(user_id, guven=yeni_guven, streak=0)

        try:
            if yeni_guven < 30:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"🚨 *Kritik Güven Uyarısı*\n"
                        f"Güven puanınız {yeni_guven}'e düştü!\n"
                        f"Görevlerinizi aksatmaya devam ederseniz görevden alma oylaması başlatılır."
                    ),
                    parse_mode="Markdown",
                )
            elif yeni_guven < 50:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"⚠️ *Güven Uyarısı*\n"
                        f"Güven puanınız {yeni_guven}'e düştü. Görevlerinizi yapın!"
                    ),
                    parse_mode="Markdown",
                )
        except Exception:
            pass


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("profil", profil_komutu))
    app.add_handler(CommandHandler("makam", makam_komutu))
    app.add_handler(CommandHandler("gorev", gorev_yap_komutu))
    app.add_handler(CommandHandler("liderler", liderler_komutu))
    app.add_handler(CommandHandler("rol_ver", rol_ver))
    app.add_handler(CommandHandler("rol_al", rol_al))
    app.add_handler(CommandHandler("duyuru", duyuru))
    app.add_handler(CommandHandler("puan_ver", puan_ver))
    app.add_handler(CommandHandler("guven_ver", guven_ver))
    app.add_handler(CallbackQueryHandler(buton_handler))

    job_queue = app.job_queue
    job_queue.run_daily(
        gunluk_ceza_isle,
        time=datetime.strptime("23:59", "%H:%M").time(),
        name="gunluk_ceza",
    )

    logger.info("Bot başlatılıyor...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
