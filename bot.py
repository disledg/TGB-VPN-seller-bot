
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update 
from telegram.ext import Application, CallbackQueryHandler, CommandHandler, ContextTypes 
from db import User, VPNServer, Transaction, Subscription
from db import get_db_session
from db import init_db, SessionLocal
from db_operations import last_subscription, create_user , get_sub_list,buy_sub
from sqlalchemy import desc

import json

from datetime import datetime

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

    if session.query(User).filter(User.telegram_id == str(update.callback_query.from_user.id)).first() == None:
        create_user(str(update.callback_query.from_user.id),update.effective_user.username) 
    user = session.query(User).filter(User.telegram_id == str(update.callback_query.from_user.id)).first()

    subscription = last_subscription(session=session,user=user)

    loading_message = await context.bot.send_message(chat_id=update.callback_query.message.chat.id, text="Загрузка...")
    loading_message_id = loading_message.message_id  # Сохраняем ID сообщения

    if not subscription:
        await loading_message_id.edit_text(
            f'Профиль {user.username}, {user.telegram_id}\nВы не приобретали ещё у нас подписку, но это явно стоит сделать:)\nВаш счёт составляет: {user.balance}'
        )
    # Проверяем, истекла ли подписка
    elif subscription.expiry_date < datetime.now():
        await loading_message_id.edit_text(
            f'Ваш профиль {user.username}, {user.telegram_id}, Ваша подписка действует до - {subscription.expiry_date}'
        )
    else:
        await loading_message_id.edit_text(
            f'Ваш профиль {user.username}, {user.telegram_id},\nВаша подписка истекла - {subscription.expiry_date}'
        )


async def about(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account")
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(f'Игорь чё нить напишет, я продублирую',reply_markup=reply_markup)

async def support(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
        InlineKeyboardButton("Написать", callback_data="sup") # Нужно через каллбек доделать 
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(f'Что бы отправить сообщение поддержке выберите в меню кнопку "Написать", а далее изложите в одном сообщении свою ошибку.',reply_markup=reply_markup)

async def pop_up(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(f'Когда нибудь эта штука заработает',reply_markup=reply_markup)

async def buy_subscription(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    session = next(get_db_session())
    user = session.query(User).filter(User.telegram_id == str(update.callback_query.from_user.id)).first()
    check = last_subscription(session=session,user=user)

    if not check:
        keyboard = [
        [
            InlineKeyboardButton("Тариф 1 \"Бимжик\"", callback_data="Бимжик"),
        ],
        [
            InlineKeyboardButton("Тариф 2 \"Бизнес хомячёк\"", callback_data="Бизнес_хомячёк"),
        ],
        [
            InlineKeyboardButton("Тариф 3 \"Продвинутый Акулёнок\"", callback_data="Продвинутый_Акулёнок"),
        ],
        [
            InlineKeyboardButton("Главное меню", callback_data="account"),
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(f'Какую подписку вы хотели бы приобрести\nТариф 1 "Бимжик" - 200 рубликов - 1 месяцок\nТариф 2 "Бизнес хомячёк" - 500 рубликов - 3 месяцка\nТариф 3 "Продвинутый Акулёнок" - 888 рубликов - 6 месяцков\n',reply_markup=reply_markup)
    # проверяем, истекла ли подписка
    else:
        keyboard = [
        [
            InlineKeyboardButton("Главное меню", callback_data="account"),
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(f'У вас уже приобретена подписка',reply_markup=reply_markup)


async def faq(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text(f'Когда нибудь что нибудь здесь будет написано!!;)',reply_markup=reply_markup)

async def button_handler(update: Update, context):
    query = update.callback_query

    loading_message = await query.message.reply_text("Загрузка...")
    
    await query.answer()

    session = next(get_db_session())
    try:
        if query.data == 'account':
            await personal_account(update, context=context)
        elif query.data == 'about':
            await about(update, context)
        elif query.data == 'support':
            await support(update, context)
        elif query.data == 'pop_up':
            await pop_up(update, context)
        elif query.data == 'buy_tarif':
            await buy_subscription(update, context)
        elif query.data == 'faq':
            await faq(update, context)
        elif query.data == 'payment_history':
            await active_sub(update, context)
        
        if query.data in ['Бимжик', 'Бизнес_хомячёк', 'Продвинутый_Акулёнок']:
            plan = query.data.replace('_', ' ') if '_' in query.data else query.data
            check = buy_sub(session, query.from_user.id, plan, logger)

            
            if check != "OK":
                await loading_message.edit_text("Неизвестный тариф.")
            else:
                await loading_message.edit_text("Тариф успешно установлен!")

    except Exception as e:
        logger.error(f"Ошибка при обработке запроса пользователя {query.from_user.id}: {e}")
        await loading_message.edit_text("Произошла ошибка. Пожалуйста, попробуйте снова.")
    finally:
        session.close()



async def active_sub(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
    [
        InlineKeyboardButton("Главное меню", callback_data="account"),
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    session = next(get_db_session())
    list_sub = get_sub_list(session, 10, update.callback_query.from_user.id)

    if list_sub:  
        message = "Ваши подписки:\n"
        for cur_sub in list_sub: 
            if cur_sub.expiry_date > datetime.now():
                message += f"   Активная: {cur_sub.plan}, Дата покупки: {cur_sub.created_at}\n"
            else:
                message += f"   Устаревшая: {cur_sub.plan}, Дата покупки: {cur_sub.created_at}\n"
    else: 
        message = "Ты пидор, не приобрел у нас подписку?!"
    await update.callback_query.message.reply_text(message,reply_markup=reply_markup)

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
    application.add_handler(CallbackQueryHandler(button_handler))
    

    application.run_polling(allowed_updates=Update.ALL_TYPES)
    db.close()


if __name__ == "__main__":
    main()
