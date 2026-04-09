import os
from dotenv import load_dotenv

load_dotenv()

CSRF_SECRET_KEY = os.getenv("CSRF_SECRET_KEY")