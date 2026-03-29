import os
from dotenv import load_dotenv
import urllib.parse
load_dotenv()

class Config:
    user = os.getenv('DB_USERNAME')
    pw = os.getenv('DB_PASSWORD')
    host = os.getenv('DB_HOST')
    db_name = os.getenv('DB_NAME')
    safe_password = urllib.parse.quote_plus(pw) if pw else ""
    SQLALCHEMY_DATABASE_URI = f'mysql://{user}:{safe_password}@{host}/{db_name}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')