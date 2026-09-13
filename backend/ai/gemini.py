import time
import requests

from backend.config.config import (
    GEMINI_API_KEY,
    GEMINI_MODELS,
    GEMINI_API_URL,
    AI_TEMPERATURE,
    AI_MAX_OUTPUT_TOKENS,
    AI_TIMEOUT_SECONDS,
)


# ============================================================
# HeyManAI
# Gemini API Engine
# ============================================================
#
# দায়িত্ব:
#
# 1. Gemini API request
# 2. Model fallback
# 3. Retry
# 4. Response extraction
#
# AI-এর personality / behavior এখানে নেই।
# Behavior AnswerBuilder.java থেকে আসবে।
#
# ============================================================


MODEL_RETRY_COUNT = 2
RETRY_DELAY_SECONDS = 2


# ============================================================
# PROMPT BUILDER
# ============================================================

def build_prompt(
    message,
    memory_text=""
):
    """
    AnswerBuilder.java থেকে পাওয়া prompt
    Gemini-তে পাঠানোর জন্য প্রস্তুত করে।

    এখানে কোনো personality বা behavior
    যোগ করা হবে না।
    """

    if memory_text:
        return (
            f"{memory_text}\n\n"
            f"{message}"
        )

    return message


# ============================================================
# GEMINI REQUEST
# ============================================================

def _request_model(
    model,
    prompt
):
    """
    একটি নির্দিষ্ট Gemini model-এ request পাঠায়।
    """

    if not GEMINI_API_KEY:

        return {
            "success": False,
            "status": 500,
            "retryable": False,
            "error": "GEMINI_API_KEY is not configured."
        }

    url = GEMINI_API_URL.format(
        model=model,
        api_key=GEMINI_API_KEY
    )

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": prompt
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": AI_TEMPERATURE,
            "maxOutputTokens": AI_MAX_OUTPUT_TOKENS
        }
    }

    try:

        response = requests.post(
            url,
            json=payload,
            timeout=AI_TIMEOUT_SECONDS
        )

        # ----------------------------------------------------
        # SUCCESS
        # ----------------------------------------------------

        if response.status_code == 200:

            try:
                data = response.json()

            except ValueError:

                return {
                    "success": False,
                    "status": 502,
                    "retryable": False,
                    "error": (
                        "Gemini returned invalid JSON."
                    )
                }

            answer = extract_answer(data)

            if answer:

                return {
                    "success": True,
                    "status": 200,
                    "answer": answer,
                    "model": model
                }

            return {
                "success": False,
                "status": 502,
                "retryable": False,
                "error": (
                    "Gemini returned an empty response."
                )
            }

        # ----------------------------------------------------
        # RATE LIMIT
        # ----------------------------------------------------

        if response.status_code == 429:

            return {
                "success": False,
                "status": 429,
                "retryable": True,
                "error": response.text
            }

        # ----------------------------------------------------
        # SERVER / TEMPORARY ERROR
        # ----------------------------------------------------

        if 500 <= response.status_code <= 599:

            return {
                "success": False,
                "status": response.status_code,
                "retryable": True,
                "error": response.text
            }

        # ----------------------------------------------------
        # OTHER ERROR
        # ----------------------------------------------------

        return {
            "success": False,
            "status": response.status_code,
            "retryable": False,
            "error": response.text
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "status": 503,
            "retryable": True,
            "error": "Gemini request timed out."
        }

    except requests.exceptions.ConnectionError as error:

        return {
            "success": False,
            "status": 503,
            "retryable": True,
            "error": (
                f"Gemini connection error: {error}"
            )
        }

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "status": 503,
            "retryable": True,
            "error": (
                f"Gemini request error: {error}"
            )
        }

    except Exception as error:

        return {
            "success": False,
            "status": 500,
            "retryable": False,
            "error": (
                f"Unexpected Gemini error: {error}"
            )
        }


# ============================================================
# ASK GEMINI
# ============================================================

def ask_gemini(
    message=None,
    memory_text="",
    user_message=None,
    memory=None
):
    """
    Gemini model chain চালায়।

    message:
        server.py থেকে আসা user message।

    user_message:
        backward compatibility-এর জন্য রাখা হয়েছে।

    memory_text / memory:
        আগের memory।
    """

    # --------------------------------------------------------
    # MESSAGE COMPATIBILITY
    # --------------------------------------------------------

    if message is None:
        message = user_message

    if message is None:
        message = ""

    message = str(message).strip()

    # --------------------------------------------------------
    # MEMORY COMPATIBILITY
    # --------------------------------------------------------

    if not memory_text and memory:
        memory_text = memory

    if memory_text is None:
        memory_text = ""

    # --------------------------------------------------------
    # EMPTY MESSAGE
    # --------------------------------------------------------

    if not message:

        return {
            "success": False,
            "status": 400,
            "answer": "",
            "model": "",
            "error": "User message is empty."
        }

    # --------------------------------------------------------
    # BUILD PROMPT
    # --------------------------------------------------------

    prompt = build_prompt(
        message,
        memory_text
    )

    # --------------------------------------------------------
    # NO MODEL
    # --------------------------------------------------------

    if not GEMINI_MODELS:

        return {
            "success": False,
            "status": 500,
            "answer": "",
            "model": "",
            "error": (
                "No Gemini models are configured."
            )
        }

    errors = []

    # ========================================================
    # MODEL FALLBACK CHAIN
    # ========================================================

    for model in GEMINI_MODELS:

        model = model.strip()

        if not model:
            continue

        for attempt in range(
            MODEL_RETRY_COUNT
        ):

            result = _request_model(
                model,
                prompt
            )

            # ------------------------------------------------
            # SUCCESS
            # ------------------------------------------------

            if result.get("success"):

                return result

            # ------------------------------------------------
            # ERROR
            # ------------------------------------------------

            error_message = result.get(
                "error",
                "Unknown Gemini error."
            )

            errors.append(
                f"{model} "
                f"(attempt {attempt + 1}): "
                f"{error_message}"
            )

            # ------------------------------------------------
            # NON-RETRYABLE
            # ------------------------------------------------

            if not result.get(
                "retryable",
                False
            ):
                break

            # ------------------------------------------------
            # RETRY
            # ------------------------------------------------

            if attempt < MODEL_RETRY_COUNT - 1:

                time.sleep(
                    RETRY_DELAY_SECONDS
                )

    # ========================================================
    # ALL MODELS FAILED
    # ========================================================

    return {
        "success": False,
        "status": 503,
        "answer": "",
        "model": "",
        "error": (
            "All Gemini models failed.\n"
            + "\n".join(errors)
        )
    }


# ============================================================
# RESPONSE EXTRACTION
# ============================================================

def extract_answer(data):
    """
    Gemini JSON response থেকে শুধু text বের করে।
    """

    try:

        candidates = data.get(
            "candidates",
            []
        )

        if not candidates:
            return ""

        candidate = candidates[0]

        content = candidate.get(
            "content",
            {}
        )

        parts = content.get(
            "parts",
            []
        )

        texts = []

        for part in parts:

            text = part.get("text")

            if text:
                texts.append(
                    str(text)
                )

        return "\n".join(
            texts
        ).strip()

    except Exception:

        return ""