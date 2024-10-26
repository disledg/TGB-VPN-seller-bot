from db import User, Subscription, Transaction, VPNServer
import string
import secrets
import json
from sqlalchemy import desc
from dateutil.relativedelta import relativedelta
from datetime import datetime
from db import get_db_session
from panel import PanelInteraction


def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))


# Загрузка конфигурации один раз
with open('config.json', 'r') as file:
    config = json.load(file)


class UserService:
    def __init__(self, logger):
        self.logger = logger

    def add_user(self, telegram_id: int):
        session = next(get_db_session())
        try:
            new_user = User(telegram_id=telegram_id, username=generate_random_string())
            session.add(new_user)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Ошибка при добавлении пользователя: {e}")
        finally:
            session.close()

    def get_user_by_telegram_id(self, telegram_id: int):
        session = next(get_db_session())
        try:
            return session.query(User).filter(User.telegram_id == telegram_id).first()
        except Exception as e:
            self.logger.error(f"Ошибка при получении пользователя: {e}")
        finally:
            session.close()

    def add_transaction(self, user_id: int, amount: float):
        session = next(get_db_session())
        try:
            transaction = Transaction(user_id=user_id, amount=amount)
            session.add(transaction)
            session.commit()
        except Exception as e:
            self.logger.error(f"Ошибка добавления транзакции: {e}")
        finally:
            session.close()

    def update_balance(self, telegram_id: int, amount: float):
        session = next(get_db_session())
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.balance = amount
                self.add_transaction(user.id, amount)
                session.commit()
            else:
                self.logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден.")
        except Exception as e:
            session.rollback()
            self.logger.error(f"Ошибка при обновлении баланса: {e}")
        finally:
            session.close()

    def last_subscription(self, user):
        session = next(get_db_session())
        try:
            return (
                session.query(Subscription)
                .filter(Subscription.user_id == user.id)
                .order_by(desc(Subscription.created_at))
                .first()
            )
        except Exception as e:
            self.logger.error(f"Ошибка при получении последней подписки: {e}")
        finally:
            session.close()

    def tariff_setting(self, user, plan: str, expiry_duration: int):
        session = next(get_db_session())
        try:
            server = (
                session.query(VPNServer)
                .filter(VPNServer.current_users < VPNServer.max_users)
                .order_by(VPNServer.current_users.asc())
                .first()
            )

            if not server:
                self.logger.error("Нет доступных VPN серверов.")
                return "120"

            # Рассчитываем дату окончания подписки
            expiry_ = datetime.now() + relativedelta(months=expiry_duration)
            self.logger.info(f"Создание подписки для пользователя {user.id} на сервере {server.id} с планом {plan} до {expiry_}")

            new_subscription = Subscription(user_id=user.id, vpn_server_id=server.id, plan=plan, expiry_date=expiry_)
            session.add(new_subscription)
            session.commit()

            self.logger.info(f"Подписка успешно создана для пользователя {user.id}")
            return "OK"
        except Exception as e:
            self.logger.error(f"Ошибка в установке тарифа: {e}")
            return "Ошибка"
        finally:
            session.close()

    def buy_sub(self, telegram_id: str, plan: str):
        session = next(get_db_session())
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                self.logger.error(f"Пользователь с Telegram ID {telegram_id} не найден.")
                return "error"

            current_plan = config['subscription_templates'].get(plan)
            if not current_plan:
                self.logger.error(f"Тариф {plan} не найден в шаблонах.")
                return "error"

            cost = current_plan['cost']
            if user.balance >= cost:
                user.balance -= cost
                session.commit()
                result = self.tariff_setting(user, plan, current_plan['duration'])
                if result == "OK":
                    add_server_result = self.add_to_server(telegram_id)
                    if add_server_result == "OK":
                        return "OK"
                    else:
                        return "ERROR " + add_server_result
                else:
                    return "ERROR " + result

            self.logger.error(f"Недостаточно средств на счету пользователя {telegram_id} для тарифа {plan}.")
            return 100

        except Exception as e:
            self.logger.error(f"Ошибка при покупке тарифа для пользователя {telegram_id}: {e}")
            session.rollback()
        finally:
            session.close()

    def get_sub_list(self, count: int, user_id: int):
        session = next(get_db_session())
        try:
            return (
                session.query(Subscription)
                .filter(Subscription.user_id == user_id)
                .order_by(desc(Subscription.created_at))
                .limit(count)
                .all()
            )
        except Exception as e:
            self.logger.error(f"Ошибка при получении списка подписок для пользователя {user_id}: {e}")

    def add_to_server(self, telegram_id: str):
        session = next(get_db_session())
        try:
            user_sub = (
                session.query(Subscription)
                .join(User)
                .filter(User.telegram_id == telegram_id)
                .first()
            )
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            server = session.query(VPNServer).filter(VPNServer.id == user_sub.vpn_server_id).first()

            url_base = f"https://{server.ip_address}:{server.port}/{server.secret}"
            login_data = {
                'username': server.login,
                'password': server.password,
            }

            # Преобразование server.config из строки в словарь
            try:
                server_config_dict = json.loads(server.config)
            except json.JSONDecodeError as e:
                self.logger.error(f"Ошибка разбора JSON: {e}")
                return "180"

            client_id = server_config_dict['obj']['id']
            panel = PanelInteraction(url_base, login_data, self.logger)
            panel.add_client(client_id, user_sub.expiry_date.isoformat(), user.username)
            return "OK"
        except Exception as e:
            self.logger.error(f"Ошибка при установке на сервер для пользователя {telegram_id}: {e}")
            return "ERROR"

    def create_uri(self, telegram_id: str):
        session = next(get_db_session())
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if not user:
                self.logger.error(f"Пользователь с Telegram ID {telegram_id} не найден.")
                return "error"

            sub = self.last_subscription(user)
            if not sub:
                self.logger.error("Подписка не найдена.")
                return "error"

            vpn_server = session.query(VPNServer).filter_by(id=sub.vpn_server_id).first()
            base_url = f"https://{vpn_server.ip_address}:{vpn_server.port}/{vpn_server.secret}"
            login_data = {
                'username': vpn_server.login,
                'password': vpn_server.password
            }

            server_config_dict = json.loads(vpn_server.config)
            client_id = server_config_dict['obj']['id']

            PI = PanelInteraction(base_url, login_data, self.logger)
            CIF3 = PI.get_client_traffic(user.username)  # Client Info From 3x-ui 
            VPNCIF3 = PI.getInboundInfo(client_id)
            return self.generate_uri(vpn_config=VPNCIF3, CIF3=CIF3)
        except Exception as e:
            self.logger.error(f"Ошибка в создании URI: {e}")
            return "error"
        finally:
            session.close()

    def generate_uri(self, vpn_config, CIF3):
        try:
            # Проверяем тип vpn_config и загружаем его, если это строка
            config_data = json.loads(vpn_config) if isinstance(vpn_config, str) else vpn_config

            obj = config_data["obj"]
            port = obj["port"]

            # Обрабатываем настройки клиентов
            clients = json.loads(obj["settings"])["clients"] if isinstance(obj["settings"], str) else obj["settings"]["clients"]

            for client in clients:
                if client["email"] == CIF3['obj']['email']:
                    uuid = client["id"]
                    flow = client["flow"]

                    # Извлечение параметров из streamSettings
                    stream_settings = json.loads(obj["streamSettings"]) if isinstance(obj["streamSettings"], str) else obj["streamSettings"]
                    dest = stream_settings["realitySettings"]["dest"]
                    server_names = stream_settings["realitySettings"]["serverNames"]
                    public_key = stream_settings["realitySettings"]["settings"]["publicKey"]
                    fingerprint = stream_settings["realitySettings"]["settings"]["fingerprint"]
                    short_id = stream_settings["realitySettings"]["shortIds"][0]  # Первый короткий ID

                    # Сборка строки VLess
                    return (
                        f"vless://{uuid}@{dest}:{port}?type=tcp&security=reality"
                        f"&pbk={public_key}&fp={fingerprint}&sni={server_names[0]}"
                        f"&sid={short_id}&spx=%2F&flow={flow}#user-{CIF3}"
                    )

            self.logger.error(f"Клиент с email {CIF3} не найден.")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка в методе создания URI: {e}")
            return None
