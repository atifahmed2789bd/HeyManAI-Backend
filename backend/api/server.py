from flask import Flask, request, jsonify

from backend.config.config import (
    API_HOST,
    API_PORT,
    DEBUG_MODE,
)

from backend.ai.gemini import ask_gemini

from backend.memory.memory import (
    save_message,
    get_relevant_memory,
)


# ============================================================
# HeyManAI API Server
# ============================================================

app = Flask(__name__)

# Large JSON request/response support.
# Do not impose a small request-size limit here.
app.config["MAX_CONTENT_LENGTH"] = None


# ============================================================
# Home
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "service": "HeyManAI API",
        "status": "online"
    })


# ============================================================
# Health
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "service": "HeyManAI API",
        "status": "healthy"
    })


# ============================================================
# Chat
# ============================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        # ----------------------------------------------------
        # Read JSON
        # ----------------------------------------------------

        data = request.get_json(
            silent=True
        )

        if not isinstance(data, dict):

            return jsonify({
                "success": False,
                "error": "Invalid JSON request."
            }), 400


        # ----------------------------------------------------
        # Read message
        # ----------------------------------------------------

        message = data.get(
            "message"
        )

        if not isinstance(
            message,
            str
        ):

            return jsonify({
                "success": False,
                "error": "Message must be a string."
            }), 400


        message = message.strip()


        if not message:

            return jsonify({
                "success": False,
                "error": "Message is empty."
            }), 400


        # ----------------------------------------------------
        # Save user message
        # ----------------------------------------------------

        save_message(
            role="user",
            content=message
        )


        # ----------------------------------------------------
        # Retrieve relevant memory
        # ----------------------------------------------------

        memory = get_relevant_memory(
            message
        )


        # ----------------------------------------------------
        # Ask Gemini
        # ----------------------------------------------------

        result = ask_gemini(
            message=message,
            memory=memory
        )


        # ----------------------------------------------------
        # Check Gemini result
        # ----------------------------------------------------

        if not isinstance(
            result,
            dict
        ):

            return jsonify({
                "success": False,
                "error": "Invalid Gemini response."
            }), 500


        if not result.get(
            "success",
            False
        ):

            return jsonify({
                "success": False,
                "error": result.get(
                    "error",
                    "Gemini request failed."
                )
            }), 500


        # ----------------------------------------------------
        # Get answer
        # ----------------------------------------------------

        answer = result.get(
            "answer",
            ""
        )


        if not isinstance(
            answer,
            str
        ):

            return jsonify({
                "success": False,
                "error": "AI response is invalid."
            }), 500


        answer = answer.strip()


        if not answer:

            return jsonify({
                "success": False,
                "error": "AI returned an empty response."
            }), 500


        # ----------------------------------------------------
        # Save assistant response
        # ----------------------------------------------------

        save_message(
            role="assistant",
            content=answer
        )


        # ----------------------------------------------------
        # Return complete response
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "answer": answer
        })


    # ========================================================
    # Error Handling
    # ========================================================

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# Server Start
# ============================================================

if __name__ == "__main__":

    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=DEBUG_MODE
    )