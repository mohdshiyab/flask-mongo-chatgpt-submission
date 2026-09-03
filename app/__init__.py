import logging
from flask import Flask
from app.config import Config
from app.db import get_mongo_client, get_db, init_db
from app.routes import api_bp

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def create_app(test_config=None, mongo_client=None):
    app = Flask(__name__)
    app.config.from_object(Config)

    if test_config:
        app.config.update(test_config)

    # Database initialization
    db = None
    if "DB" in app.config:
        db = app.config["DB"]
    else:
        try:
            client = mongo_client or get_mongo_client(app.config.get("MONGO_URI"))
            db = get_db(client, app.config.get("MONGO_DB_NAME"))
            app.config["DB"] = db
            init_db(db)
        except Exception as e:
            logger.warning(f"Could not connect or initialize MongoDB at startup: {e}")

    # Register blueprints
    app.register_blueprint(api_bp)

    return app
