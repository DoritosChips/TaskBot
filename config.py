import os
from dotenv import load_dotenv

load_dotenv()

host = os.environ.get('db-host')
user = os.environ.get('db-user')
password = os.environ.get('db-password')
db_name="taskbot"