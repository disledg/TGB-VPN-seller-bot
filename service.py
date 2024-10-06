from db import User
from db import Subscription
from db import Transaction
from db import VPNServer
from datetime import datetime,timedelta
from db import get_db_session
import json 
from panel import PanelInteraction

with open('config.json', 'r') as file : config = json.load(file)

class UserService:
    def __init__(self,logger):
        self.logger = logger
        
    def add_user(self,telegram_id: int, username: str):
        session = next(get_db_session())
        try:
            new_user = User(telegram_id=telegram_id, username=username)
            session.add(new_user)
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Ошибка при добавлении пользователя: {e}")
        finally:
            session.close()

    def get_user_by_telegram_id(self,telegram_id: int):
        session = next(get_db_session())
        try:
            return session.query(User).filter(User.telegram_id == telegram_id).first()
        except Exception as e:
            self.logger.error(f"Ошибка при получении пользователя: {e}")
        finally:
            session.close()

    def add_transaction(self,user_id: int,amount: float):
        session = next(get_db_session())
        try:
            transaction = Transaction(user_id = user_id,amount = amount) 
            session.add(transaction)
            session.commit()
        except Exception as e:
            self.logger.error(f"Ошибка добавления транзакции:{e}")
        finally:
            session.close()

    def pop_up_balance(self,telegram_id: int,amount: float):
        session = next(get_db_session())
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                user.balance = amount
                self.add_transaction(user.id,amount)
                session.commit()
            else:
                self.logger.warning(f"Пользователь с Telegram ID {telegram_id} не найден.")
        except Exception as e:
            self.logger.error(f"Ошибка при обновлении баланса:{e}")
            self.logger.error(f"Сумма: {amount}, Пользователь: {telegram_id}")
            session.rollback() 
        finally:
            session.close()

    def tariff_setting(self,telegram_id: int,plan: str):
        session = next(get_db_session())
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                server = (
                session.query(VPNServer)
                .filter(VPNServer.current_users < VPNServer.max_users)
                .order_by(VPNServer.current_users.asc())
                .first())
                current_plan = config['subscription_templates'].get(plan)
                expiry_ = datetime.now() + timedelta(days=current_plan['expiry_duration'])
                new_subscription = Subscription(user_id = user.id,vpn_server_id = server.id,plan = plan,expiry_date = expiry_)
                session.add(new_subscription)
                session.commit()
        except Exception as e:
            self.logger.error(f"Чё то ошибка в установке тарифа: {e}")
        finally:
            session.close()


    def create_uri(self,telegram_id,):
        session = next(get_db_session())
        try:
            user = session.query(User).filter(User.telegram_id == telegram_id).first()
            if user:
                subscription = user.subscriptions
                if not subscription:
                    return None 
                vpn_server = session.query(VPNServer).filter_by(id=subscription.vpn_server_id).first()
                baseURL ="http://" + vpn_server.ip_address + ":" + vpn_server.port
                PI = PanelInteraction(baseURL,vpn_server.login_data,self.logger)
                CIF3 = PI.get_client_traffic(user.username) # Client Info From 3x-ui 
                URI = self.generate_uri(vpn_config=vpn_server.config,CIF3=CIF3)
                session.commit()
                return URI
        except Exception as e:
            self.logger.error(f"Чё то ошибка в создании uri: {e}")
        finally:
            session.close()


    def generate_uri(self, vpn_config, CIF3):
        try:
            # Извлечение необходимых данных из конфигурации
            config_data = json.loads(vpn_config)
            obj = config_data["obj"]
            port = obj["port"]
            clients = json.loads(obj["settings"])["clients"]

            # Поиск клиента по email (CIF3)
            for client in clients:
                if client["email"] == CIF3:
                    uuid = client["id"]
                    flow = client["flow"]
                    
                    # Извлечение параметров из streamSettings
                    stream_settings = json.loads(obj["streamSettings"])
                    dest = stream_settings["realitySettings"]["dest"]
                    server_names = stream_settings["realitySettings"]["serverNames"]
                    public_key = stream_settings["realitySettings"]["settings"]["publicKey"]
                    fingerprint = stream_settings["realitySettings"]["settings"]["fingerprint"]
                    short_id = stream_settings["realitySettings"]["shortIds"][0]  # Первый короткий ID

                    # Сборка строки VLess
                    URI = (
                        f"vless://{uuid}@{dest}:{port}?type=tcp&security=reality"
                        f"&pbk={public_key}&fp={fingerprint}&sni={server_names[0]}"
                        f"&sid={short_id}&spx=%2F&flow={flow}#user-{CIF3}"
                    )
                    
                    return URI

            # Если клиент с указанным email не найден
            self.logger.warning(f"Клиент с email {CIF3} не найден.")
            return None

        except Exception as e:
            self.logger.error(f"Ошибка в методе создания uri: {e}")
            return None

