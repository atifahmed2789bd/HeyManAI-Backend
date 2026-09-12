from flask import Flask, request, jsonify

from backend.config.config import (
    API_HOST,
    API_PORT,
    DEBUG_MODE,
)

from backend.ai.gemini import ask_gemini

from backend.memory.memory import (
    save_message,
)


# ============================================================
# HeyManAI API Server
# ============================================================

app = Flask(__name__)


# ------------------------------------------------------------
# Root
# ------------------------------------------------------------

@app.route("/", methods=["GET"])
def root():
    return jsonify({
        "success": True,
        "service": "HeyManAI Backend",
        "status": "online"
    })


# ------------------------------------------------------------
# Health Check
# ------------------------------------------------------------

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "success": True,
        "status": "healthy"
    })


# ------------------------------------------------------------
# Chat API
# ------------------------------------------------------------

@app.route("/api/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(
            silent=True
        )

        if not data:
            return jsonify({
                "success": False,
                "answer": "",
                "error": "Invalid JSON request."
            }), 400

        message = data.get(
            "message",
            ""
        )

        prompt = data.get(
            "prompt",
            ""
        )

        # ----------------------------------------------------
        # Prompt is preferred when Android sends a full prompt.
        # Otherwise use message directly.
        # ----------------------------------------------------

        if prompt and str(prompt).strip():
            gemini_input = str(prompt).strip()

        elif message and str(message).strip():
            gemini_input = str(message).strip()

        else:
            return jsonify({
                "success": False,
                "answer": "",
                "error": "Message is required."
            }), 400

        # ----------------------------------------------------
        # Save original user message
        # ----------------------------------------------------

        if message and str(message).strip():
            save_message(
                "user",
                str(message).strip()
            )

        # ----------------------------------------------------
        # Send prompt to Gemini
        # ----------------------------------------------------

        result = ask_gemini(
            gemini_input
        )

        if not result.get("success"):
            return jsonify({
                "success": False,
                "answer": "",
                "error": result.get(
                    "error",
                    "Gemini request failed."
                )
            }), 502

        answer = result.get(
            "answer",
            ""
        ).strip()

        if not answer:
            return jsonify({
                "success": False,
                "answer": "",
                "error": "Empty AI response."
            }), 502

        # ----------------------------------------------------
        # Save assistant response
        # ----------------------------------------------------

        save_message(
            "assistant",
            answer
        )

        # ----------------------------------------------------
        # Return response to Android
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "answer": answer
        })

    except Exception as error:
        return jsonify({
            "success": False,
            "answer": "",
            "error": str(error)
        }), 500


# ------------------------------------------------------------
# Start Server
# ------------------------------------------------------------

if __name__ == "__main__":
    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=DEBUG_MODE
    )
