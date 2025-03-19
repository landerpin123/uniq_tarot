from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
import logging
from config import TOKEN, TIMEZONE
from tarot_cards import tarot_deck
from database import init_db, get_user, update_user
from pytz import timezone
import random
import sqlite3

# Инициализация БД
init_db()

# Логирование
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    handlers=[logging.FileHandler("bot.log"), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# Конфигурация раскладов
SPREADS = {
    "1 карта": {"price": 10, "cards": 1},
    "3 карты": {"price": 25, "cards": 3},
    "Кельтский крест": {"price": 50, "cards": 10},
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        if not get_user(user_id):
            with sqlite3.connect('tarot.db') as conn:
                conn.execute(
                    "INSERT INTO users (user_id) VALUES (?)", 
                    (user_id,)
                )
        await update.message.reply_text(
            "🔮 Добро пожаловать!\n"
            "Для регистрации введите /register"
        )
    except Exception as e:
        logger.error(f"Ошибка в /start: {e}")
        await update.message.reply_text("⚠️ Ошибка инициализации!")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        user = get_user(user_id)
        if user['registered']:
            await update.message.reply_text("❌ Вы уже зарегистрированы!")
            return
            
        await update.message.reply_text("📝 Введите ваше имя и фамилию:")
        update_user(user_id, registered=1)
        
    except Exception as e:
        logger.error(f"Ошибка регистрации: {e}")
        await update.message.reply_text("⚠️ Ошибка регистрации!")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    try:
        text = update.message.text
        user = get_user(user_id)
        
        if not user['name']:
            update_user(user_id, name=text)
            await update.message.reply_text("📅 Введите дату рождения (ДД.ММ.ГГГГ):")
        elif not user['birth_date']:
            update_user(user_id, birth_date=text, balance=100)
            await update.message.reply_text(
                f"🎉 Регистрация завершена!\n"
                f"Баланс: 100💰\n"
                f"Используйте /tarot для расклада"
            )
    except Exception as e:
        logger.error(f"Ошибка обработки текста: {e}")

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Ошибка: {context.error}")
    if update.effective_message:
        await update.effective_message.reply_text("⚠️ Произошла ошибка. Попробуйте позже.")

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Обработчики
    handlers = [
        CommandHandler("start", start),
        CommandHandler("register", register),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    # Обработчик ошибок
    application.add_error_handler(error_handler)
    
    # Настройка времени
    tz = timezone(TIMEZONE)
    if application.job_queue:
        application.job_queue.scheduler.configure(timezone=tz)
    
    application.run_polling()

if __name__ == "__main__":
    main()