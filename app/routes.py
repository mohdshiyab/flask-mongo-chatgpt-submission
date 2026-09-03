import logging
from flask import Blueprint, request, jsonify, current_app, render_template
from app.db import get_db, get_prompts_collection, get_history_collection
from app.services import (
    get_prompt_template,
    format_prompt,
    call_chatgpt,
    call_chatgpt_batch_async,
    save_history,
    save_batch_history
)

logger = logging.getLogger(__name__)

api_bp = Blueprint("api", __name__)


@api_bp.route("/", methods=["GET"])
@api_bp.route("/ui", methods=["GET"])
def index():
    """Serve interactive web frontend."""
    return render_template("index.html")


@api_bp.route("/api", methods=["GET"])
def api_info():
    return jsonify({
        "name": "Flask + MongoDB + ChatGPT Service",
        "endpoints": {
            "single_prompt": "POST /api/ask",
            "batch_prompt": "POST /api/ask-batch",
            "history": "GET /api/history",
            "prompts": "GET /api/prompts",
            "health": "GET /api/health"
        }
    })



@api_bp.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@api_bp.route("/api/prompts", methods=["GET"])
def list_prompts():
    """List all stored prompt templates."""
    try:
        db = current_app.config.get("DB", get_db())
        collection = get_prompts_collection(db)
        prompts = list(collection.find({}))
        return jsonify({"prompts": prompts}), 200
    except Exception as e:
        logger.error(f"Error fetching prompts: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/history", methods=["GET"])
def list_history():
    """Retrieve history of requests and responses."""
    try:
        db = current_app.config.get("DB", get_db())
        collection = get_history_collection(db)
        limit = min(int(request.args.get("limit", 50)), 100)
        records = list(collection.find({}).sort("created_at", -1).limit(limit))
        for r in records:
            r["_id"] = str(r["_id"])
        return jsonify({"history": records, "count": len(records)}), 200
    except Exception as e:
        logger.error(f"Error fetching history: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500


@api_bp.route("/api/ask", methods=["POST"])
@api_bp.route("/ask", methods=["POST"])
def ask():
    """
    Step 1 to Step 5:
    Accepts single userinput, replaces {{userinput}} in template from MongoDB,
    calls ChatGPT, saves to history, and returns {"response": "..."}.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body. Expected JSON object with 'userinput'."}), 400

    userinput = data.get("userinput")
    if userinput is None or not isinstance(userinput, str) or not userinput.strip():
        return jsonify({"error": "Field 'userinput' is required and must be a non-empty string."}), 400

    prompt_id = data.get("prompt_id", "Education_Prompt")
    db = current_app.config.get("DB", get_db())

    # Step 2: Fetch template from prompts collection
    try:
        template = get_prompt_template(db, prompt_id=prompt_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Database error retrieving prompt: {e}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    # Step 3: Replace {{userinput}} and call ChatGPT API
    formatted_prompt = format_prompt(template, userinput.strip())
    client = current_app.config.get("OPENAI_CLIENT")
    model = current_app.config.get("OPENAI_MODEL")

    try:
        response_text = call_chatgpt(prompt=formatted_prompt, client=client, model=model)
    except Exception as e:
        logger.error(f"ChatGPT API call error: {e}", exc_info=True)
        return jsonify({"error": f"ChatGPT API error: {str(e)}"}), 502

    # Step 4: Save Request/Response into history collection
    try:
        save_history(
            db=db,
            userinput=userinput.strip(),
            prompt_id=prompt_id,
            prompt_used=formatted_prompt,
            response=response_text
        )
    except Exception as e:
        logger.warning(f"Failed to record history to MongoDB: {e}")

    # Step 5: Return Response in JSON format
    return jsonify({"response": response_text}), 200


@api_bp.route("/api/ask-batch", methods=["POST"])
@api_bp.route("/ask-batch", methods=["POST"])
@api_bp.route("/batch-ask", methods=["POST"])
@api_bp.route("/api/batch-ask", methods=["POST"])
def ask_batch():
    """
    Step 6:
    Accepts a list of strings in one request, fetches prompt from MongoDB,
    processes each string independently asynchronously with ChatGPT API,
    and returns a list of AI responses in the same order.
    """
    data = request.get_json(silent=True)
    if not data or not isinstance(data, dict):
        return jsonify({"error": "Invalid JSON body. Expected JSON object with 'userinputs'."}), 400

    userinputs = data.get("userinputs")
    if userinputs is None:
        userinputs = data.get("userinput")

    if not isinstance(userinputs, list) or len(userinputs) == 0:
        return jsonify({"error": "Field 'userinputs' is required and must be a non-empty list of strings."}), 400

    for idx, item in enumerate(userinputs):
        if not isinstance(item, str) or not item.strip():
            return jsonify({"error": f"Item at index {idx} must be a non-empty string."}), 400

    prompt_id = data.get("prompt_id", "Education_Prompt")
    db = current_app.config.get("DB", get_db())

    # Fetch prompt from NoSQL
    try:
        template = get_prompt_template(db, prompt_id=prompt_id)
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Database error retrieving prompt: {e}", exc_info=True)
        return jsonify({"error": f"Database error: {str(e)}"}), 500

    # Format all prompts
    formatted_prompts = [format_prompt(template, u.strip()) for u in userinputs]

    # Process each string independently with ChatGPT API asynchronously
    async_client = current_app.config.get("ASYNC_OPENAI_CLIENT")
    model = current_app.config.get("OPENAI_MODEL")

    try:
        responses = call_chatgpt_batch_async(
            prompts=formatted_prompts,
            client=async_client,
            model=model
        )
    except Exception as e:
        logger.error(f"Batch ChatGPT API call error: {e}", exc_info=True)
        return jsonify({"error": f"ChatGPT API error: {str(e)}"}), 502

    # Save every request/response pair into history collection
    try:
        history_records = [
            {
                "prompt_id": prompt_id,
                "userinput": u.strip(),
                "prompt_used": fp,
                "response": resp
            }
            for u, fp, resp in zip(userinputs, formatted_prompts, responses)
        ]
        save_batch_history(db, history_records)
    except Exception as e:
        logger.warning(f"Failed to record batch history to MongoDB: {e}")

    # Return list of AI responses in the same order
    return jsonify({"responses": responses}), 200
