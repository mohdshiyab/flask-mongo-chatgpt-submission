import json


def test_health_check(client):
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_frontend_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"ChatGPT + MongoDB Service" in response.data



def test_prompts_seeded(client, mock_mongo_db):
    response = client.get("/api/prompts")
    assert response.status_code == 200
    data = response.get_json()
    prompts = data.get("prompts", [])
    assert any(p["_id"] == "Education_Prompt" for p in prompts)


def test_ask_single_success(client, mock_mongo_db):
    payload = {
        "userinput": "How much should I score in each subject to pass CA final?"
    }
    response = client.post(
        "/api/ask",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "response" in data
    assert "You are an expert in education domain. Answer the following: How much should I score in each subject to pass CA final?" in data["response"]

    # Verify history collection in MongoDB
    history_coll = mock_mongo_db["history"]
    records = list(history_coll.find({"prompt_id": "Education_Prompt"}))
    assert len(records) == 1
    assert records[0]["userinput"] == "How much should I score in each subject to pass CA final?"
    assert records[0]["response"] == data["response"]
    assert "created_at" in records[0]


def test_ask_single_validation(client):
    # Empty body
    res = client.post("/api/ask", data=json.dumps({}), content_type="application/json")
    assert res.status_code == 400

    # Non-string userinput
    res = client.post("/api/ask", data=json.dumps({"userinput": 123}), content_type="application/json")
    assert res.status_code == 400

    # Non-existent prompt_id
    res = client.post(
        "/api/ask",
        data=json.dumps({"userinput": "Test query", "prompt_id": "NonExistent_Prompt"}),
        content_type="application/json"
    )
    assert res.status_code == 404


def test_ask_batch_success(client, mock_mongo_db):
    queries = [
        "How much should I score in each subject to pass CA final?",
        "What are the subjects in CA Final Group 1?",
        "What is the passing criteria for both groups together?"
    ]
    payload = {
        "userinputs": queries
    }
    response = client.post(
        "/api/ask-batch",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "responses" in data
    assert len(data["responses"]) == len(queries)

    # Verify order preservation
    for idx, query in enumerate(queries):
        assert query in data["responses"][idx]

    # Verify history collection has 3 records stored
    history_coll = mock_mongo_db["history"]
    records = list(history_coll.find({"prompt_id": "Education_Prompt"}))
    assert len(records) >= len(queries)
    saved_inputs = [r["userinput"] for r in records]
    for q in queries:
        assert q in saved_inputs


def test_ask_batch_validation(client):
    # Empty list
    res = client.post("/api/ask-batch", data=json.dumps({"userinputs": []}), content_type="application/json")
    assert res.status_code == 400

    # Non-list
    res = client.post("/api/ask-batch", data=json.dumps({"userinputs": "just a string"}), content_type="application/json")
    assert res.status_code == 400

    # List with non-string
    res = client.post("/api/ask-batch", data=json.dumps({"userinputs": ["valid", 123]}), content_type="application/json")
    assert res.status_code == 400


def test_history_endpoint(client, mock_mongo_db):
    # Insert sample record
    mock_mongo_db["history"].insert_one({
        "prompt_id": "Education_Prompt",
        "userinput": "Sample question",
        "prompt_used": "Sample prompt",
        "response": "Sample response",
        "created_at": "2026-09-03T12:00:00Z"
    })
    response = client.get("/api/history")
    assert response.status_code == 200
    data = response.get_json()
    assert data["count"] >= 1
    assert any(r["userinput"] == "Sample question" for r in data["history"])


def test_ask_batch_alternative_key(client):
    # Client sends 'userinput' as a list instead of 'userinputs'
    payload = {
        "userinput": ["Question 1", "Question 2"]
    }
    response = client.post(
        "/api/ask-batch",
        data=json.dumps(payload),
        content_type="application/json"
    )
    assert response.status_code == 200
    data = response.get_json()
    assert "responses" in data
    assert len(data["responses"]) == 2

