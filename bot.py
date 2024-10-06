
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update 
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes 
from db import User, VPNServer, Transaction, Subscription
from db import last_subscription, create_user , get_sub_list
import db
from sqlalchemy import desc
import json
import string
from datetime import datetime
from db import get_db_session
from db import init_db, SessionLocal
from logger_config import setup_logger
with open('config.json', 'r') as file:
    config = json.load(file)


logger = setup_logger()


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

    if session.query(User).filter(User.telegram_id == str(update.effective_user.id)).first() == None:
        create_user(str(update.effective_user.id),update.effective_user.username) 
    user = session.query(User).filter(User.telegram_id == str(update.effective_user.id)).first()

    subscription = last_subscription(session=session,user=user)

    if not subscription:
        await update.message.reply_text(f'Профиль {user.username}\nВы не приобретали ещё у нас подписку, но это явно стоит сделать:)',reply_markup=reply_markup)
    # проверяем, истекла ли подписка
    elif subscription.expiry_date < datetime.now():
        await update.message.reply_text(f'Ваш профиль {user.username},Ваша подписка действует до - {subscription.expiry_date}',reply_markup=reply_markup)
    else:
        await update.message.reply_text(f'Ваш профиль {user.username},\nВаша подписка истекла - {subscription.expiry_date}',reply_markup=reply_markup)

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

async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    session = next(get_db_session())
    user = session.query(User).filter(User.telegram_id == str(update.effective_user.id)).first()
    check = last_subscription(session=session,user=user)

    if not check:
        keyboard = [
        [
            InlineKeyboardButton("Тариф 1 \"Бимжик\"", callback_data="bimzhik"),
        ],
        [
            InlineKeyboardButton("Тариф 2 \"Бизнес хомячёк\"", callback_data="homyachok"),
        ],
        [
            InlineKeyboardButton("Тариф 2 \"Продвинутый Акулёнок\"", callback_data="akulenok"),
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f'Какую подписку вы хотели бы приобрести\nТариф 1 "Бимжик" - 200 рубликов - 1 месяцок\nТариф 2 "Бизнес хомячёк" - 500 рубликов - 3 месяцка\nТариф 3 "Продвинутый Акулёнок" - 888 рубликов - 888 рубликов\n',reply_markup=reply_markup)
    # проверяем, истекла ли подписка
    else:
        keyboard = [
        [
            InlineKeyboardButton("Главное меню", callback_data="account"),
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f'У вас уже приобретена подписка',reply_markup=reply_markup)


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(f'Когда нибудь что нибудь здесь будет написано!!;)',reply_markup=reply_markup)
async def active_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    session = next(get_db_session())
    list_sub = get_sub_list(session, 10, update.effective_user.id)

    if list_sub:  
        message = "Ваши подписки:\n"
        for cur_sub in list_sub: 
            if cur_sub.expiry_date > datetime.now():
                message += f"   Активная: {cur_sub.plan}, Дата покупки: {cur_sub.created_at}\n"
            else:
                message += f"   Устаревшая: {cur_sub.plan}, Дата покупки: {cur_sub.created_at}\n"
    else: 
        message = "Ты пидор, не приобрел у нас подписку?!"
    await update.message.reply_text(message,reply_markup=reply_markup)

def main() -> None:
    
    init_db()
    db = SessionLocal()
    application = Application.builder().token(config['token']).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("account", personal_account))
    application.add_handler(CommandHandler("about", about))
    application.add_handler(CommandHandler("support", support))
    application.add_handler(CommandHandler("popup", pop_up))
    application.add_handler(CommandHandler("buy_subscription", buy_subscription))
    application.add_handler(CommandHandler("faq", faq))
    application.add_handler(CommandHandler("active_sub", active_sub))
    

    application.run_polling(allowed_updates=Update.ALL_TYPES)
    db.close()


if __name__ == "__main__":
    main()
