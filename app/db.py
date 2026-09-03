import logging
from pymongo import MongoClient
from app.config import Config

logger = logging.getLogger(__name__)

DEFAULT_EDUCATION_PROMPT = {
    "_id": "Education_Prompt",
    "template": "You are an expert in education domain. Answer the following: {{userinput}}"
}

_mongo_client = None


def get_mongo_client(uri: str = None):
    global _mongo_client
    if _mongo_client is None:
        mongo_uri = uri or Config.MONGO_URI
        _mongo_client = MongoClient(mongo_uri, serverSelectionTimeoutMS=2000)
    return _mongo_client


def get_db(client=None, db_name: str = None):
    if client is None:
        client = get_mongo_client()
    database_name = db_name or Config.MONGO_DB_NAME
    return client[database_name]


def get_prompts_collection(db=None):
    if db is None:
        db = get_db()
    return db["prompts"]


def get_history_collection(db=None):
    if db is None:
        db = get_db()
    return db["history"]


def init_db(db=None):
    """Seed initial prompt template if not already present."""
    if db is None:
        db = get_db()
    try:
        prompts = get_prompts_collection(db)
        existing = prompts.find_one({"_id": DEFAULT_EDUCATION_PROMPT["_id"]})
        if not existing:
            prompts.insert_one(DEFAULT_EDUCATION_PROMPT)
            logger.info("Initialized default Education_Prompt in MongoDB.")
        else:
            logger.info("Education_Prompt already exists in MongoDB.")
    except Exception as e:
        logger.warning(f"Could not initialize default prompt in MongoDB: {e}")
