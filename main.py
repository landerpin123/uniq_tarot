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
import random
from pytz import timezone

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация раскладов
SPREADS = {
    "1 карта": {"price": 10, "cards": 1},
    "3 карты": {"price": 25, "cards": 3},
    "Кельтский крест": {"price": 50, "cards": 10},
}

# Хранилище данных пользователей
users = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    users[user_id] = {
        "balance": 0,
        "registered": False,
        "name": None,
        "birth_date": None,
        "current_spread": None,
        "selected_cards": [],
        "deck": [],
    }
    
    await update.message.reply_text(
        "🔮 Добро пожаловать в Таро-Бота!\n"
        "Для регистрации введите /register"
    )

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if users[user_id]["registered"]:
        await update.message.reply_text("❌ Вы уже зарегистрированы!")
        return
    
    users[user_id]["registered"] = True
    await update.message.reply_text(
        "✅ Регистрация успешна!\n"
        "Введите ваше имя и фамилию:"
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text
    
    if not users[user_id]["registered"]:
        await update.message.reply_text("⚠️ Сначала зарегистрируйтесь через /register")
        return
    
    if not users[user_id]["name"]:
        users[user_id]["name"] = text
        await update.message.reply_text("📅 Введите дату рождения (ДД.ММ.ГГГГ):")
    elif not users[user_id]["birth_date"]:
        users[user_id]["birth_date"] = text
        users[user_id]["balance"] = 100  # Стартовый баланс
        await update.message.reply_text(
            f"🎉 Привет, {users[user_id]['name']}!\n"
            f"Ваш баланс: {users[user_id]['balance']}💰\n"
            "Используйте /tarot для начала работы"
        )

async def tarot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if not users.get(user_id, {}).get("registered"):
        await update.message.reply_text("⚠️ Сначала зарегистрируйтесь через /register")
        return
    
    keyboard = [
        [InlineKeyboardButton(spread, callback_data=f"spread_{spread}")]
        for spread in SPREADS
    ]
    await update.message.reply_text(
        "🔮 Выберите расклад:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def spread_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    spread_name = query.data.split("_")[1]
    
    if users[user_id]["balance"] < SPREADS[spread_name]["price"]:
        await query.edit_message_text("❌ Недостаточно средств! Пополните баланс.")
        return
    
    users[user_id]["current_spread"] = spread_name
    users[user_id]["balance"] -= SPREADS[spread_name]["price"]
    users[user_id]["deck"] = random.sample(tarot_deck, len(tarot_deck))
    users[user_id]["selected_cards"] = []
    
    await show_card_selection(query, user_id)

async def show_card_selection(query, user_id):
    current_card = len(users[user_id]["selected_cards"]) + 1
    total_cards = SPREADS[users[user_id]["current_spread"]]["cards"]
    
    keyboard = [
        [InlineKeyboardButton(card["name"], callback_data=f"card_{idx}")]
        for idx, card in enumerate(users[user_id]["deck"][:10])
    ]
    
    await query.edit_message_text(
        text=f"🃏 Выбор карты {current_card}/{total_cards}:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def card_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    card_idx = int(query.data.split("_")[1])
    
    users[user_id]["selected_cards"].append(users[user_id]["deck"][card_idx])
    total_needed = SPREADS[users[user_id]["current_spread"]]["cards"]
    
    if len(users[user_id]["selected_cards"]) < total_needed:
        await show_card_selection(query, user_id)
    else:
        result = "\n\n".join(
            f"{i+1}. {card['name']}: {card['meaning']}"
            for i, card in enumerate(users[user_id]["selected_cards"])
        )
        await query.edit_message_text(
            f"📜 {users[user_id]['name']}, ваш расклад:\n\n{result}\n"
            f"Остаток баланса: {users[user_id]['balance']}💰"
        )

def main():
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков
    handlers = [
        CommandHandler("start", start),
        CommandHandler("register", register),
        CommandHandler("tarot", tarot_handler),
        CallbackQueryHandler(spread_callback, pattern="^spread_"),
        CallbackQueryHandler(card_callback, pattern="^card_"),
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
    ]
    
    for handler in handlers:
        application.add_handler(handler)
    
    # Настройка временной зоны
    application.job_queue.scheduler.configure(timezone=timezone(TIMEZONE))
    
    application.run_polling()

if __name__ == "__main__":
    main()