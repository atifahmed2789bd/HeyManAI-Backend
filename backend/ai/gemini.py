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
# এই ফাইলের দায়িত্ব শুধুমাত্র:
#
# 1. Gemini API request
# 2. Model fallback
# 3. Retry
# 4. Response extraction
# 5. Error handling
#
# IMPORTANT:
#
# AI personality / behavior / instructions এখানে নেই।
#
# সম্পূর্ণ behavior এবং master prompt
# AnswerBuilder.java থেকে আসবে।
#
# ============================================================


MODEL_RETRY_COUNT = 2
RETRY_DELAY_SECONDS = 2


# ============================================================
# GEMINI REQUEST
# ============================================================

def _request_model(
    model,
    prompt
):
    """
    একটি নির্দিষ্ট Gemini model-এ request পাঠায়।

    এখানে prompt পরিবর্তন করা হয় না।
    AnswerBuilder.java থেকে পাওয়া prompt
    সরাসরি Gemini API-তে পাঠানো হয়।
    """

    if not GEMINI_API_KEY:

        return {
            "success": False,
            "status": 500,
            "retryable": False,
            "error": "GEMINI_API_KEY is not configured."
        }


    if not model:

        return {
            "success": False,
            "status": 500,
            "retryable": False,
            "error": "Gemini model is empty."
        }


    if not prompt:

        return {
            "success": False,
            "status": 400,
            "retryable": False,
            "error": "Gemini prompt is empty."
        }


    # --------------------------------------------------------
    # API URL
    # --------------------------------------------------------

    url = GEMINI_API_URL.format(
        model=model,
        api_key=GEMINI_API_KEY
    )


    # --------------------------------------------------------
    # REQUEST PAYLOAD
    # --------------------------------------------------------

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


    # ========================================================
    # HTTP REQUEST
    # ========================================================

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


            answer = extract_answer(
                data
            )


            if answer:

                return {
                    "success": True,
                    "status": 200,
                    "answer": answer,
                    "model": model
                }


            # ------------------------------------------------
            # EMPTY RESPONSE
            # ------------------------------------------------

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
                "error": (
                    "Gemini rate limit reached: "
                    + response.text
                )
            }


        # ----------------------------------------------------
        # TEMPORARY SERVER ERROR
        # ----------------------------------------------------

        if 500 <= response.status_code <= 599:

            return {
                "success": False,
                "status": response.status_code,
                "retryable": True,
                "error": (
                    "Gemini server error: "
                    + response.text
                )
            }


        # ----------------------------------------------------
        # OTHER HTTP ERROR
        # ----------------------------------------------------

        return {
            "success": False,
            "status": response.status_code,
            "retryable": False,
            "error": (
                "Gemini HTTP "
                + str(response.status_code)
                + ": "
                + response.text
            )
        }


    # ========================================================
    # TIMEOUT
    # ========================================================

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "status": 503,
            "retryable": True,
            "error": "Gemini request timed out."
        }


    # ========================================================
    # CONNECTION ERROR
    # ========================================================

    except requests.exceptions.ConnectionError as error:

        return {
            "success": False,
            "status": 503,
            "retryable": True,
            "error": (
                "Gemini connection error: "
                + str(error)
            )
        }


    # ========================================================
    # REQUEST ERROR
    # ========================================================

    except requests.exceptions.RequestException as error:

        return {
            "success": False,
            "status": 503,
            "retryable": True,
            "error": (
                "Gemini request error: "
                + str(error)
            )
        }


    # ========================================================
    # UNKNOWN ERROR
    # ========================================================

    except Exception as error:

        return {
            "success": False,
            "status": 500,
            "retryable": False,
            "error": (
                "Unexpected Gemini error: "
                + str(error)
            )
        }


# ============================================================
# ASK GEMINI
# ============================================================

def ask_gemini(
    prompt=None,
    message=None,
    memory_text="",
    user_message=None,
    memory=None
):
    """
    Gemini model fallback chain চালায়।

    নতুন architecture:

        AnswerBuilder.java
                ↓
             prompt
                ↓
            server.py
                ↓
          ask_gemini(prompt)
                ↓
             Gemini

    prompt থাকলে সেটিই সরাসরি Gemini-তে যাবে।

    message / user_message / memory
    শুধুমাত্র backward compatibility-এর জন্য রাখা হয়েছে।
    """


    # ========================================================
    # PROMPT SELECTION
    # ========================================================

    #
    # নতুন system-এ prompt-ই প্রধান।
    #

    if prompt is not None:

        prompt = str(
            prompt
        ).strip()


    # ========================================================
    # BACKWARD COMPATIBILITY
    # ========================================================

    #
    # পুরোনো code যদি prompt না পাঠায়,
    # তাহলে message ব্যবহার করা যাবে।
    #

    if not prompt:

        if message is None:

            message = user_message


        if message is None:

            message = ""


        message = str(
            message
        ).strip()


        #
        # পুরোনো memory support।
        #

        if not memory_text and memory:

            memory_text = memory


        if memory_text is None:

            memory_text = ""


        memory_text = str(
            memory_text
        ).strip()


        #
        # পুরোনো flow-এর জন্য prompt তৈরি।
        #
        # নতুন AnswerBuilder flow-এ এই অংশ ব্যবহার হবে না,
        # কারণ সেখানে prompt সরাসরি দেওয়া হবে।
        #

        if memory_text:

            prompt = (
                memory_text
                + "\n\n"
                + message
            )

        else:

            prompt = message


    # ========================================================
    # EMPTY PROMPT
    # ========================================================

    if not prompt:

        return {
            "success": False,
            "status": 400,
            "answer": "",
            "model": "",
            "error": "Gemini prompt is empty."
        }


    # ========================================================
    # MODEL CHECK
    # ========================================================

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

        if model is None:

            continue


        model = str(
            model
        ).strip()


        if not model:

            continue


        # ----------------------------------------------------
        # RETRY CURRENT MODEL
        # ----------------------------------------------------

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

            if result.get(
                "success",
                False
            ):

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
            # NON-RETRYABLE ERROR
            # ------------------------------------------------

            if not result.get(
                "retryable",
                False
            ):

                break


            # ------------------------------------------------
            # RETRY DELAY
            # ------------------------------------------------

            if attempt < (
                MODEL_RETRY_COUNT - 1
            ):

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

def extract_answer(
    data
):
    """
    Gemini JSON response থেকে শুধু text বের করে।
    """

    try:

        if not isinstance(
            data,
            dict
        ):

            return ""


        candidates = data.get(
            "candidates",
            []
        )


        if not isinstance(
            candidates,
            list
        ):

            return ""


        if not candidates:

            return ""


        candidate = candidates[0]


        if not isinstance(
            candidate,
            dict
        ):

            return ""


        content = candidate.get(
            "content",
            {}
        )


        if not isinstance(
            content,
            dict
        ):

            return ""


        parts = content.get(
            "parts",
            []
        )


        if not isinstance(
            parts,
            list
        ):

            return ""


        texts = []


        for part in parts:

            if not isinstance(
                part,
                dict
            ):

                continue


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