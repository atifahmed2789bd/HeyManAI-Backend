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
# 1. Gemini API-তে request পাঠানো
# 2. একাধিক Gemini model fallback করা
# 3. Temporary API error হলে retry করা
# 4. Gemini response থেকে text বের করা
#
# গুরুত্বপূর্ণ:
#
# AI-এর আচরণ / personality / response style
# এখানে নির্ধারণ করা হবে না।
#
# এসব নির্দেশনা AnswerBuilder.java থেকে আসবে।
#
# ============================================================


MODEL_RETRY_COUNT = 2
RETRY_DELAY_SECONDS = 2


# ============================================================
# PROMPT BUILDER
# ============================================================

def build_prompt(user_message, memory_text=""):
    """
    Gemini-তে পাঠানোর জন্য basic prompt তৈরি করে।

    এখানে কোনো personality বা behavior instruction নেই।
    AnswerBuilder.java থেকে পাওয়া prompt/message 그대로
    Gemini-তে পাঠানো হবে।
    """

    if memory_text:
        return (
            f"{memory_text}\n\n"
            f"{user_message}"
        )

    return user_message


# ============================================================
# GEMINI REQUEST
# ============================================================

def _request_model(model, prompt):
    """
    একটি নির্দিষ্ট Gemini model-এ request পাঠায়।
    """

    if not GEMINI_API_KEY:
        return {
            "success": False,
            "status": 500,
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
        # Success
        # ----------------------------------------------------

        if response.status_code == 200:

            try:
                data = response.json()
            except ValueError:
                return {
                    "success": False,
                    "status": 502,
                    "error": "Gemini returned invalid JSON."
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
                "error": "Gemini returned an empty response."
            }

        # ----------------------------------------------------
        # Retryable errors
        # ----------------------------------------------------

        if response.status_code == 429:

            return {
                "success": False,
                "status": 429,
                "retryable": True,
                "error": response.text
            }

        if 500 <= response.status_code <= 599:

            return {
                "success": False,
                "status": response.status_code,
                "retryable": True,
                "error": response.text
            }

        # ----------------------------------------------------
        # Non-retryable error
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
            "error": f"Gemini connection error: {error}"
        }

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "status": 503,
            "retryable": True,
            "error": f"Gemini request error: {error}"
        }

    except Exception as error:

        return {
            "success": False,
            "status": 500,
            "retryable": False,
            "error": f"Unexpected Gemini error: {error}"
        }


# ============================================================
# ASK GEMINI
# ============================================================

def ask_gemini(user_message, memory_text=""):
    """
    Gemini model chain চালায়।

    একটি model ব্যর্থ হলে পরের model ব্যবহার করবে।
    প্রতিটি model temporary error হলে retry করবে।
    """

    prompt = build_prompt(
        user_message,
        memory_text
    )

    if not GEMINI_MODELS:

        return {
            "success": False,
            "status": 500,
            "answer": "",
            "model": "",
            "error": "No Gemini models are configured."
        }

    errors = []

    # ========================================================
    # MODEL FALLBACK CHAIN
    # ========================================================

    for model in GEMINI_MODELS:

        for attempt in range(
            MODEL_RETRY_COUNT
        ):

            result = _request_model(
                model,
                prompt
            )

            # ------------------------------------------------
            # Successful response
            # ------------------------------------------------

            if result.get("success"):

                return result

            # ------------------------------------------------
            # Error information
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
            # Non-retryable error
            # ------------------------------------------------

            if not result.get(
                "retryable",
                False
            ):
                break

            # ------------------------------------------------
            # Retry delay
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
    Gemini JSON response থেকে শুধুমাত্র answer text বের করে।
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

            text = part.get(
                "text"
            )

            if text:
                texts.append(
                    str(text)
                )

        return "\n".join(
            texts
        ).strip()

    except Exception:
        return ""