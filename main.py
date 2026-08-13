from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ConversationHandler,
    filters
)
from telegram import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
import os
from dotenv import load_dotenv
import weatherforcast
from llmapi import generate
import logging
import db_utils as db


db.ensure_user_table()


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()
API_TOKEN = os.getenv("BOT_TOKEN")
if not API_TOKEN:
    raise ValueError("BOT_TOKEN environment variable is not set.")


async def ask_takeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(  # type: ignore[arg-type]
        "Hangi kalkış pistini kullanmak istiyorsun?\nİsmini yazar mısın?"
    )
    return 1


async def ask_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # type: ignore[arg-type]
    takeoff_name = (update.message.text or "").strip()
    db.update_user(update.effective_user, takeoff=takeoff_name)

    keyboard = [
        [KeyboardButton("📍 Pist konumumu paylaş", request_location=True)]]
    location_markup = ReplyKeyboardMarkup(
        keyboard, one_time_keyboard=True, resize_keyboard=True)

    await update.message.reply_text(  # type: ignore[arg-type]
        "Son olarak pistin GPS konumunu paylaşır mısın?",
        reply_markup=location_markup
    )
    return 2


async def save_location(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.location:
        await update.message.reply_text("Konum bilgisi alamadım, lütfen konumu paylaş.")
        return 2

    lat = update.message.location.latitude
    lon = update.message.location.longitude

    db.update_user(update.effective_user, lat=lat, lon=lon)
    user_data = db.get_user(update.effective_user.id)
    await update.message.reply_text(  # type: ignore[arg-type]
        (
            "Kayıt tamamlandı!\n"
            f"Kalkış pisti: {user_data.get('takeoff') or '—'}\n"
            f"Pistin bulunduğu il: {user_data.get('city')}\n"
            f"Koordinatlar: {lat:.4f}, {lon:.4f}"
        ),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def set_takeoff():
    return ConversationHandler(
        entry_points=[CommandHandler("settakeoff", ask_takeoff)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_takeoff)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_location)],
            2: [MessageHandler(filters.LOCATION, save_location)],
        },
        fallbacks=[],
    )


# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = update.effective_user
    print(user_data)
    db.create_user(user_data)
    await update.message.reply_text(  # type: ignore[arg-type]
        (
            f"Merhaba {user_data.first_name}! Ben senin Yamaç Paraşütü botunum 🤖"
            "\nSana yamaç paraşütü ile ilgili bilgiler verebilirim."
            "\nYardım için /yardım komutunu kullanabilirsin."
        )
    )


# /yardım
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Komutlar:"  # type: ignore
        "\n/start - Botu başlat"
        "\n/help - Yardım"
        "\n/city - Bulunduğunu şehrin hava durumu bilgisi"
        "\n/takeoff - Kayıtlı pistin için hava durumu bilgisi"
        "\n/settakeoff - Kayıtlı pistini ayarla"
        "\n/setcity - Kayıtlı şehri ayarla"
        "\n/llm <mesaj> - Büyük dil modeli ile sohbet et (deneysel)"
        "\n/todo - Yapılacaklar listesi"
    )


# /city
async def city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    if user_data is None or not user_data.get("forcast_city"):
        await update.message.reply_text(  # type: ignore[arg-type]
            "Şehrin kayıtlı değil. Lütfen önce /setcity komutunu kullanarak şehrini kaydet."
        )
        return
    text = weatherforcast.get_takeoff_forcast(user_data.get("forcast_city"))
    text = (f"```\n {text}\n```")
    await update.message.reply_text(text, parse_mode="Markdown")


# /takeoff
async def takeoff(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = db.get_user(update.effective_user.id)
    if user_data is None or not user_data.get("takeoff") or not user_data.get("lat") or not user_data.get("lon"):
        await update.message.reply_text(  # type: ignore[arg-type]
            "Kalkış pistin veya konumun kayıtlı değil. Lütfen önce /settakeoff komutunu kullanarak pistini ve konumunu kaydet."
        )
        return
    text = weatherforcast.get_takeoff_forcast([user_data.get("takeoff"),
                                               user_data.get("city")],
                                              user_data.get("lat"),
                                              user_data.get("lon"))
    text = (f"```\n {text}\n```")
    await update.message.reply_text(text, parse_mode="Markdown")
    return


async def ask_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Hangi şehri kullanmak istiyorsun?"
        "\nİsmini yazar mısın?"
    )
    return 1


async def save_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = (update.message.text or "").strip()
    print(f"City: {city}")
    city = db.get_is_valid_city(city)

    if not db.get_is_valid_city(city):
        # type: ignore
        await update.message.reply_text("Yanlış şehir ismi girdin, lütfen tekrar dene.")
        return 1

    db.update_user(update.effective_user, forcast_city=city)

    await update.message.reply_text(  # type: ignore[arg-type]
        (
            "Kayıt tamamlandı!\n"
            f"Şehir: {city}"
        ),
        reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


# /setcity
def set_city():
    return ConversationHandler(
        entry_points=[CommandHandler("setcity", ask_city)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_city)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_city)],
        },
        fallbacks=[],
    )


# /llm
async def llm_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Kullanıcıdan gelen metni birleştir
    prompt = " ".join(context.args).strip() if context.args else ""
    if not prompt:
        # type: ignore
        await update.message.reply_text("Kullanım: /llm <mesaj>"
                                        "\nÖrnek: /llm Yamaç paraşütü nedir?")
    else:
        logger.info(f"LLM prompt: {prompt}")
        yanit = generate(prompt)
        logger.info(f"LLM yanıtı: {yanit}")
        # pyright: ignore[reportOptionalMemberAccess]
        await update.message.reply_text(yanit)
    return


# todo
async def todo_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    prompt = (
        "Bu Bot için ileride yapılması planlananlar:"
        "\n- Daha fazla şehir için hava durumu"
        "\n- Kullanıcıdan şehir bilgisi alma"
        "\n- Hava durumu uyarıları"
        "\n- Yamaç paraşütü ile ilgili sıkça sorulan sorular"
        "\n- Yamaç paraşütü ile ilgili temel bilgiler"
        "\n- Yamaç paraşütü ile ilgili güvenlik ipuçları"
        "\n- Yamaç paraşütü ile ilgili ekipman bilgileri"
        "\n- Yamaç paraşütü ile ilgili eğitim kaynakları"
        "\n- Yamaç paraşütü ile ilgili haberler ve etkinlikler"
        "\n- Kullanıcı geri bildirimleri ve öneriler"
        "\n- Botun performansını ve yanıt hızını artırma"
        "\n- Daha gelişmiş LLM entegrasyonu ve özellikleri"
        "\n- Kullanıcı dostu arayüz ve deneyim iyileştirmeleri"
    )
    await update.message.reply_text(prompt)
    return


def main():
    app = Application.builder().token(API_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("city", city))
    app.add_handler(CommandHandler("takeoff", takeoff))
    app.add_handler(CommandHandler("llm", llm_cmd))
    app.add_handler(CommandHandler("todo", todo_cmd))

    app.add_handler(set_takeoff())
    app.add_handler(set_city())

    # app.add_handler(MessageHandler(filters.LOCATION, handle_location))

    print("Bot çalışıyor...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
