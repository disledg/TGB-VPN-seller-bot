import requests 
import uuid
import string
import secrets
import json 
from logger_config import setup_logger 
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta  

with open('config.json', 'r') as file : config = json.load(file)

def generate_date(months):
    now = datetime.now()
    
    # Преобразуем months в число
    try:
        months = int(months)  # или float(months), если месяцы могут быть дробными
    except ValueError:
        raise TypeError("months должно быть числом")

    future_date = now + timedelta(days=30 * months)
    return future_date.isoformat()


def generate_random_string(length=8):
    characters = string.ascii_letters + string.digits
    return ''.join(secrets.choice(characters) for _ in range(length))

def generate_uuid():
    return str(uuid.uuid4())


class PanelInteraction:
    def __init__(self, base_url, login_data, logger_):
        self.base_url = base_url
        self.login_data = login_data
        self.logger = logger_
        self.session_id = self.login() 
        if self.session_id:
            self.headers = {
                'Accept': 'application/json',
                'Cookie': f'3x-ui={self.session_id}',
                'Content-Type': 'application/json'
            }
        else:
            raise ValueError("Login failed, session_id is None")

    def login(self):
        login_url = self.base_url + "/login"
        response = requests.post(login_url, data=self.login_data)
        if response.status_code == 200:
            session_id = response.cookies.get("3x-ui")
            return session_id
        else:
            self.logger.error(f"Login failed: {response.status_code}")
            return None
    
    def getInboundInfo(self,inboundId):
        url = f"{self.base_url}/panel/api/inbounds/get/{inboundId}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Failed to get inbound info: {response.status_code}")
            self.logger.debug("Response:", response.text)
            return None
        

    def get_client_traffic(self, email):
        url = f"{self.base_url}/panel/api/inbounds/getClientTraffics/{email}"
        response = requests.get(url, headers=self.headers)
        if response.status_code == 200:
            return response.json()
        else:
            self.logger.error(f"Failed to get client traffic: {response.status_code}")
            self.logger.debug("Response:", response.text)
            return None

    def update_client_expiry(self, client_uuid, new_expiry_time, client_email):
        url = f"{self.base_url}/panel/api/inbounds/updateClient"
        update_data = {
            "id": 1,  
            "settings": json.dumps({
                "clients": [
                    {
                        "id": client_uuid,
                        "alterId": 0,
                        "email": client_email,  
                        "limitIp": 2,
                        "totalGB": 0,  
                        "expiryTime": new_expiry_time,
                        "enable": True,
                        "tgId": "",
                        "subId": ""
                    }
                ]
            })
        }
        response = requests.post(url, headers=self.headers, json=update_data)
        if response.status_code == 200:
            self.logger.debug("Client expiry time updated successfully.")
        else:
            self.logger.error(f"Failed to update client: {response.status_code} {response.text}")

    def add_client(self, inbound_id, months):
        url = f"{self.base_url}/panel/api/inbounds/addClient"
        client_info = {
            "clients": [
                {
                    "id": generate_uuid(),
                    "alterId": 0,
                    "email": generate_random_string(),
                    "limitIp": 2,
                    "totalGB": 0,
                    "expiryTime": generate_date(months),
                    "enable": True,
                    "tgId": "",
                    "subId": ""
                }
            ]
        }
        payload = {
            "id": inbound_id,
            "settings": json.dumps(client_info)
        }
        response = requests.post(url, headers=self.headers, json=payload)
        if response.status_code == 200:
            self.logger.debug("Client added successfully!")
            return response.json()
        else:
            self.logger.error(f"Failed to add client: {response.status_code}")
            self.logger.debug("Response:", response.text)
            return None
