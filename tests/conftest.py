import pytest
import mongomock
from unittest.mock import MagicMock, AsyncMock
from app import create_app
from app.db import init_db


@pytest.fixture
def mock_mongo_db():
    client = mongomock.MongoClient()
    db = client["test_chatgpt_service"]
    init_db(db)
    return db


@pytest.fixture
def mock_openai_client():
    mock = MagicMock()

    def fake_create(model, messages):
        prompt = messages[0]["content"] if messages else ""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = f"Mocked AI answer for: {prompt}"
        mock_response.choices = [mock_choice]
        return mock_response

    mock.chat.completions.create.side_effect = fake_create
    return mock


@pytest.fixture
def mock_async_openai_client():
    mock = MagicMock()

    async def fake_async_create(model, messages):
        prompt = messages[0]["content"] if messages else ""
        mock_response = MagicMock()
        mock_choice = MagicMock()
        mock_choice.message.content = f"Mocked Async AI answer for: {prompt}"
        mock_response.choices = [mock_choice]
        return mock_response

    mock.chat.completions.create = AsyncMock(side_effect=fake_async_create)
    return mock


@pytest.fixture
def app(mock_mongo_db, mock_openai_client, mock_async_openai_client):
    test_config = {
        "TESTING": True,
        "DB": mock_mongo_db,
        "OPENAI_CLIENT": mock_openai_client,
        "ASYNC_OPENAI_CLIENT": mock_async_openai_client,
        "OPENAI_API_KEY": "sk-test-key",
        "OPENAI_MODEL": "gpt-4o-mini"
    }
    app = create_app(test_config=test_config)
    return app


@pytest.fixture
def client(app):
    return app.test_client()
