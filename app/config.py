import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
    MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "chatgpt_service")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
    FLASK_PORT = int(os.getenv("FLASK_PORT", 5001))
    FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True").lower() in ("true", "1", "t")
    MOCK_OPENAI = os.getenv("MOCK_OPENAI", "False").lower() in ("true", "1", "t")
    OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", None)



