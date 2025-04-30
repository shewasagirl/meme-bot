import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

# Используем переменную окружения
TOKEN = os.environ["TOKEN"]
MEMES_FOLDER = "memes"

# === ДАННЫЕ ===
user_data = {}  # chat_id -> {"ratings": [...], "current_meme": int}

# === КОМАНДА /START ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_data[chat_id] = {"ratings": [], "current_meme": 0}
    await update.message.reply_text("Приветики! Сейчас будем искать тебе мемного соулмейта в FOL'GA")
    await send_meme(update, context)

# === ОТПРАВКА МЕМА ===
async def send_meme(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    data = user_data.get(chat_id)

    # Получаем список мемов в реальном времени
    memes = [os.path.join(MEMES_FOLDER, f) for f in sorted(os.listdir(MEMES_FOLDER)) if f.endswith((".jpg", ".jpeg", ".png", ".gif"))]

    if data and data["current_meme"] < len(memes):
        meme_path = memes[data["current_meme"]]

        keyboard = [[
            InlineKeyboardButton("not hehe", callback_data="0"),
            InlineKeyboardButton("hehe", callback_data="1")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        with open(meme_path, "rb") as meme_file:
            await context.bot.send_photo(chat_id=chat_id, photo=meme_file, reply_markup=reply_markup)

    else:
        await context.bot.send_message(chat_id=chat_id, text="Ну все, мемы кончились")
        await context.bot.send_message(chat_id=chat_id, text="Тебе будут приходить мэтчи, если с кем-то совпадешь. Жди и надейся! Если не дождешься, значит ты ✨unique✨")
        await find_and_notify_matches(context, chat_id)

# === ОБРАБОТКА ОЦЕНКИ ===
async def handle_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    chat_id = query.message.chat_id
    rating = int(query.data)

    await query.answer()

    # Удаляем кнопки после оценки
    await query.edit_message_reply_markup(reply_markup=None)

    data = user_data[chat_id]
    data["ratings"].append(rating)
    data["current_meme"] += 1

    await send_meme(update, context)

# === ПОИСК МЭТЧЕЙ ===
async def find_and_notify_matches(context, current_chat_id):
    current_data = user_data[current_chat_id]
    current_ratings = current_data["ratings"]

    for other_chat_id, other_data in user_data.items():
        if other_chat_id == current_chat_id:
            continue
        if len(other_data["ratings"]) != len(current_ratings):
            continue

        score = sum(1 for a, b in zip(current_ratings, other_data["ratings"]) if a == b)
        percent = score / len(current_ratings)

        if percent >= 0.6:
            try:
                user = await context.bot.get_chat(other_chat_id)
                name = f"@{user.username}" if user.username else user.first_name or "пользователь"
            except:
                name = "пользователь"

            await context.bot.send_message(
                chat_id=current_chat_id,
                text=f"Твой мэтч — {name} с совпадением {int(percent*100)}%! Иди всем расскажи!"
            )

            try:
                user = await context.bot.get_chat(current_chat_id)
                name = f"@{user.username}" if user.username else user.first_name or "пользователь"
            except:
                name = "пользователь"

            await context.bot.send_message(
                chat_id=other_chat_id,
                text=f"Совпадение с {name} на {int(percent*100)}%. Это мемомэтч!✨"
            )

# === ЗАПУСК ===
def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(handle_rating))
    print("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
