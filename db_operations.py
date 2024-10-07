
from service import UserService

#DataBase
from sqlalchemy import desc
from db import get_db_session
from db import User
from db import Subscription
from db import Transaction
from db import VPNServer

import json

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
def get_sub_list(session,count,user_id):
    subscriptions = (
        session.query(Subscription)
        .filter(Subscription.user_id == str(user_id))
        .order_by(desc(Subscription.created_at))
        .limit(count)  # Ограничиваем результат 10 записями
        .all()  # Получаем все записи
    )
    return subscriptions

def create_user(telegram_id: str, username: str = None, balance: float = 0.0):
    db = next(get_db_session())
    try:
        new_user = User(
            telegram_id=telegram_id,
            username=username,
            balance=balance
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def buy_sub(session, telegram_id: str, plan: str, logger):
    try:
        user = session.query(User).filter(User.telegram_id == str(telegram_id)).first()
        if user is None:
            logger.error(f"Пользователь с Telegram ID {telegram_id} не найден.")
            return "error"

        current_plan = config['subscription_templates'].get(plan)
        if current_plan is None:
            logger.error(f"Тариф {plan} не найден в шаблонах.")
            return "error"

        if user.balance == current_plan['cost']:
            service = UserService(logger)
            service.tariff_setting(user, plan, current_plan['duration'])
            return "OK"
        else:
            logger.error(f"Недостаточно средств на счету пользователя {telegram_id} для тарифа {plan}.")
            return "error"
    except Exception as e:
        logger.error(f"Ошибка при покупке тарифа для пользователя {telegram_id}: {e}")
