"""
Standalone script to seed initial prompt templates into MongoDB.
"""
from app.config import Config
from app.db import get_mongo_client, get_db, init_db, get_prompts_collection

def main():
    print(f"Connecting to MongoDB at: {Config.MONGO_URI}")
    print(f"Database: {Config.MONGO_DB_NAME}")
    try:
        client = get_mongo_client()
        db = get_db(client)
        init_db(db)
        prompts = list(get_prompts_collection(db).find({}))
        print("Successfully connected and initialized database!")
        print(f"Current prompts in database ({len(prompts)}):")
        for p in prompts:
            print(f" - ID: {p['_id']}")
            print(f"   Template: {p.get('template')}")
    except Exception as e:
        print(f"Error connecting to MongoDB: {e}")

if __name__ == "__main__":
    main()
