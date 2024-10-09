from sqlalchemy import create_engine, Column, String, Integer, Numeric, DateTime, ForeignKey, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import desc
from datetime import datetime
import json 
import uuid
with open('config.json', 'r') as file : config = json.load(file)

Base = declarative_base()

def generate_uuid():
    return str(uuid.uuid4())


#Пользователи
class User(Base):
    __tablename__ = 'users'

    id = Column(String, primary_key=True, default=generate_uuid)
    telegram_id = Column(String, unique=True, nullable=False)
    username = Column(String) # email 3x-ui
    balance = Column(Numeric(10, 2), default=0.0)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    subscriptions = relationship("Subscription", back_populates="user")
    transactions = relationship("Transaction", back_populates="user")

#Подписки
class Subscription(Base):
    __tablename__ = 'subscriptions'

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'))
    vpn_server_id = Column(String, ForeignKey('vpn_servers.id'))
    plan = Column(String)
    expiry_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    user = relationship("User", back_populates="subscriptions")
    vpn_server = relationship("VPNServer", back_populates="subscriptions")

#Транзакции
class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(String, primary_key=True, default=generate_uuid)
    user_id = Column(String, ForeignKey('users.id'))
    amount = Column(Numeric(10, 2))
    transaction_type = Column(String)
    created_at = Column(DateTime, default=datetime.now)

    user = relationship("User", back_populates="transactions")

class Requests(Base):
    __tablename__ = 'requests'

    id = Column(String,primary_key=True,default=generate_uuid)
    user_id = Column(String,ForeignKey('users.id'))
    username = Column(String)
    created_at = Column(DateTime,default=datetime.now)
    content = Column(String)
    status = Column(String,default='open')
    user = relationship("User",back_populates="requests")

class Administrators(Base):
    __tablename__ = 'admins'

    id =  Column(String,primary_key=True,default=generate_uuid)
    user_id = Column(String,ForeignKey('users.id'))
    admin = Column(bool,default=False)
    user = relationship("User",back_populates="admins")
# VPN-серверы
class VPNServer(Base):
    __tablename__ = 'vpn_servers'

    id = Column(String, primary_key=True, default=generate_uuid)
    server_name = Column(String)
    ip_address = Column(String)
    port = Column(Integer)
    login_data = Column(Text)   
    inbound = Column(Text)  
    config = Column(Text)  
    current_users = Column(Integer, default=0) 
    max_users = Column(Integer, default=4) 

    subscriptions = relationship("Subscription", back_populates="vpn_server")

# Настройка подключения к базе данных
DATABASE_URL = f"postgresql://{config['username']}:{config['password_DB']}@localhost/bot_db"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

