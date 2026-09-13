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

# Large request/response support.
# No small request-size limit.
app.config["MAX_CONTENT_LENGTH"] = None


# ============================================================
# HOME
# ============================================================

@app.route("/", methods=["GET"])
def home():

    return jsonify({
        "success": True,
        "service": "HeyManAI API",
        "status": "online"
    })


# ============================================================
# HEALTH
# ============================================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "success": True,
        "service": "HeyManAI API",
        "status": "healthy"
    })


# ============================================================
# CHAT
# ============================================================

@app.route("/api/chat", methods=["POST"])
def chat():

    try:

        # ----------------------------------------------------
        # READ JSON
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
        # READ USER MESSAGE
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
        # READ MASTER PROMPT
        # ----------------------------------------------------
        #
        # AnswerBuilder.java থেকে তৈরি করা সম্পূর্ণ prompt
        # এখানে গ্রহণ করা হবে।
        #
        # Backend নিজে কোনো behavior বা personality তৈরি করবে না।
        # ----------------------------------------------------

        prompt = data.get(
            "prompt"
        )

        if not isinstance(
            prompt,
            str
        ):

            return jsonify({
                "success": False,
                "error": "Prompt must be a string."
            }), 400

        prompt = prompt.strip()


        if not prompt:

            return jsonify({
                "success": False,
                "error": "Prompt is empty."
            }), 400


        # ----------------------------------------------------
        # SAVE USER MESSAGE
        # ----------------------------------------------------

        save_message(
            role="user",
            content=message
        )


        # ----------------------------------------------------
        # ASK GEMINI
        # ----------------------------------------------------
        #
        # গুরুত্বপূর্ণ:
        #
        # Gemini-কে AnswerBuilder-এর তৈরি করা prompt-ই
        # পাঠানো হচ্ছে।
        #
        # server.py কোনো নতুন behavior যোগ করছে না।
        # ----------------------------------------------------

        result = ask_gemini(
            prompt=prompt
        )


        # ----------------------------------------------------
        # CHECK GEMINI RESULT
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
        # GET ANSWER
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
        # SAVE ASSISTANT RESPONSE
        # ----------------------------------------------------

        save_message(
            role="assistant",
            content=answer
        )


        # ----------------------------------------------------
        # RETURN COMPLETE RESPONSE
        # ----------------------------------------------------

        return jsonify({
            "success": True,
            "answer": answer
        })


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ============================================================
# SERVER START
# ============================================================

if __name__ == "__main__":

    app.run(
        host=API_HOST,
        port=API_PORT,
        debug=DEBUG_MODE
    )
