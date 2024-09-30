
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update 
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes 
from db import User
from db import Subscription
from db import Transaction
from db import VPNServer
from sqlalchemy import desc
import json
from datetime import datetime
from db import get_db_session
from db import init_db, SessionLocal
from logger_config import setup_logger
with open('config.json', 'r') as file:
    config = json.load(file)

def last_subscription(session,user):
    last_subscription = (
        session.query(Subscription)
        .filter(Subscription.user_id == user.id)
        .order_by(desc(Subscription.created_at))
        .first()
    )
    return last_subscription    
    

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Личный кабинет", callback_data="account"),
        InlineKeyboardButton("О нac ;)", callback_data='about'),
    ],
        [InlineKeyboardButton("Поддержка", callback_data='support')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f'Добро пожаловать в ...! Здесь вы можете приобрести VPN. И нечего более',reply_markup=reply_markup)

async def personal_account(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Пополнить баланс", callback_data="pop_up"),
        InlineKeyboardButton("Приобрести подписку", callback_data='buy_tarif'),
    ],
        [InlineKeyboardButton("FAQ", callback_data='faq')],
        [InlineKeyboardButton("История платежей", callback_data='payment_history')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    session = next(get_db_session())
    user = session.query(User).filter(User.telegram_id == update.chat_member.from_user.id).first()
    check = last_subscription(session=session,user=user)

    if not check:
        await update.message.reply_text(f'Профиль {user.username}\nВы не приобретали ещё у нас подписку, но это явно стоит сделать:)',reply_markup=reply_markup)
    # проверяем, истекла ли подписка
    if check.expiry_date < datetime.now():
        await update.message.reply_text(f'Ваш профиль {user.username},Ваша подписка действует до - {check.expiry_date}',reply_markup=reply_markup)
    else:
        await update.message.reply_text(f'Ваш профиль {user.username},\nВаша подписка истекла - {check.expiry_date}',reply_markup=reply_markup)

async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f'Игорь чё нить напишет, я продублирую',reply_markup=reply_markup)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
        InlineKeyboardButton("Написать", callback_data="sup") # Нужно через каллбек доделать 
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f'Что бы отправить сообщение поддержке выберите в меню кнопку "Написать", а далее изложите в одном сообщении свою ошибку.',reply_markup=reply_markup)

async def pop_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f'Когда нибудь эта штука заработает',reply_markup=reply_markup)

#async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:


def main() -> None:
    logger = setup_logger()
    init_db()
    db = SessionLocal()
    application = Application.builder().token(config['token']).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("account", personal_account))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("popup", pop_up))
    #application.add_handler(CommandHandler("buy_subscription", buy_subscription))

    application.run_polling(allowed_updates=Update.ALL_TYPES)
    db.close()


if __name__ == "__main__":
    main()
