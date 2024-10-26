from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CallbackQueryHandler, ContextTypes, MessageHandler, filters
from db import User, VPNServer, Transaction, Subscription, get_db_session, init_db, SessionLocal
from sqlalchemy import desc
from service import UserService
import json
from datetime import datetime
from logger_config import setup_logger

# Чтение конфигурации и настройка логгера
with open('config.json', 'r') as file:
    config = json.load(file)
logger = setup_logger()

# Общая функция для создания клавиатуры
def create_keyboard(buttons):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)] for text, data in buttons])

# Функция для отправки сообщений с загрузкой
async def send_loading_message(update, context, text, reply_markup=None):
    loading_message = await context.bot.send_message(chat_id=update.effective_chat.id, text="Загрузка...")
    await loading_message.edit_text(text, reply_markup=reply_markup)

# Функция для обработки главного меню
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = [("Личный кабинет", "account"), ("О нас ;)", "about"), ("Поддержка", "support")]
    await send_loading_message(update, context, 'Добро пожаловать в ...! Здесь вы можете приобрести VPN. И нечего более', create_keyboard(buttons))

# Функция для обработки личного кабинета
async def personal_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = UserService(logger)
    tgid = str(update.callback_query.from_user.id)
    user = service.get_user_by_telegram_id(tgid) or service.add_user(tgid)
    subscription = service.last_subscription(user)

    buttons = [("Пополнить баланс", "pop_up"), ("Приобрести подписку", "buy_tarif"), ("❔FAQ❔", "faq"), ("История платежей", "payment_history")]
    text = (
        f'Профиль {user.username}, {user.telegram_id}\n'
        f'{"Вы не приобретали ещё у нас подписку, но это явно стоит сделать:)" if not subscription else f"Ваша подписка действует до - {subscription.expiry_date}" if subscription.expiry_date > datetime.now() else f"Ваша подписка истекла - {subscription.expiry_date}"}\n'
        f'Ваш счёт составляет: {user.balance}'
    )
    await send_loading_message(update, context, text, create_keyboard(buttons))

# Функция для отображения информации "О нас"
async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = [("Главное меню", "start")]
    await send_loading_message(update, context, 'Игорь чё нить напишет, я продублирую', create_keyboard(buttons))

# Функция для отображения поддержки
async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = [("Главное меню", "start"), ("Написать", "sup")]
    await send_loading_message(update, context, 'Для связи с поддержкой выберите "Написать" и изложите проблему в одном сообщении.', create_keyboard(buttons))

# Функция для пополнения баланса
async def pop_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = [("Главное меню", "start")]
    await send_loading_message(update, context, 'Когда-нибудь эта функция заработает', create_keyboard(buttons))

# Функция для покупки подписки
async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    service = UserService(logger)
    tgid = str(update.callback_query.from_user.id)
    user = service.get_user_by_telegram_id(tgid)
    subscription = service.last_subscription(user)
    
    if subscription is None:
        buttons = [("Тариф 1 \"Бимжик\"", "Бимжик"), ("Тариф 2 \"Бизнес хомячёк\"", "Бизнес_хомячёк"), ("Тариф 3 \"Продвинутый Акулёнок\"", "Продвинутый_Акулёнок"), ("Главное меню", "start")]
        text = 'Какую подписку вы хотите приобрести?\n1. "Бимжик" - 200 руб. на 1 месяц\n2. "Бизнес хомячёк" - 500 руб. на 3 месяца\n3. "Продвинутый Акулёнок" - 888 руб. на 6 месяцев'
    else:
        buttons = [("Главное меню", "start")]
        text = 'У вас уже приобретена подписка'
    
    await send_loading_message(update, context, text, create_keyboard(buttons))

# Функция для отображения FAQ
async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    buttons = [("Главное меню", "start")]
    await send_loading_message(update, context, 'Когда-нибудь здесь появится полезная информация!', create_keyboard(buttons))

# Функция для обработки ввода пользователя в поддержку
async def sup(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.user_data.get('awaiting_input'):
        user_input = update.message.text
        await update.message.reply_text(f"Вы ввели: {user_input}")
        context.user_data['awaiting_input'] = False
    else:
        await update.message.reply_text("Выберите команду или нажмите кнопку для продолжения.")

# Обработчик кнопок
async def button_handler(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data

    service = UserService(logger)
    tgid = str(query.from_user.id)

    try:
        if data == 'account':
            await personal_account(update, context)
        elif data == 'start':
            await start(update, context)
        elif data == 'about':
            await about(update, context)
        elif data == 'support':
            await support(update, context)
        elif data == 'sup':
            context.user_data['awaiting_input'] = True
        elif data == 'pop_up':
            await pop_up(update, context)
        elif data == 'buy_tarif':
            await buy_subscription(update, context)
        elif data == 'faq':
            await faq(update, context)
        elif data == 'payment_history':
            await active_sub(update, context)
        elif data in ['Бимжик', 'Бизнес_хомячёк', 'Продвинутый_Акулёнок']:
            plan = data.replace('_', ' ')
            result = service.buy_sub(tgid, data)
            text = {
                "OK": "Ваша конфигурация готова!",
                "100": "Недостаточно средств.",
                "120": "Нет доступных серверов, подождите немного.",
            }.get(result, "Неизвестный тариф.")
            await query.message.reply_text(text)
    except Exception as e:
        logger.error(f"Ошибка при обработке запроса пользователя {tgid}: {e}")
        await query.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте снова.")

# Запуск приложения
def main() -> None:
    init_db()
    application = Application.builder().token(config['token']).build()

    application.add_handler(CallbackQueryHandler(button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, sup))
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
