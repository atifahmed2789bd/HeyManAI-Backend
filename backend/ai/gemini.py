import requests

from backend.config.config import (
    GEMINI_API_KEY,
    AI_TEMPERATURE,
    AI_MAX_OUTPUT_TOKENS,
    AI_TIMEOUT_SECONDS,
)


# ============================================================
# HeyManAI Gemini AI
# Automatic Model Fallback System
# ============================================================


# ------------------------------------------------------------
# Gemini Models
# ------------------------------------------------------------

GEMINI_MODELS = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
]


# ------------------------------------------------------------
# Gemini API URL
# ------------------------------------------------------------

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/{model}:generateContent"
    "?key={api_key}"
)


# ------------------------------------------------------------
# Ask Gemini
# ------------------------------------------------------------

def ask_gemini(prompt):

    if not prompt or not str(prompt).strip():
        return {
            "success": False,
            "answer": "",
            "error": "Empty prompt."
        }


    if not GEMINI_API_KEY:
        return {
            "success": False,
            "answer": "",
            "error": "Gemini API key is not configured."
        }


    last_error = "All Gemini models failed."


    # --------------------------------------------------------
    # Try Models One By One
    # --------------------------------------------------------

    for model in GEMINI_MODELS:

        url = GEMINI_API_URL.format(
            model=model,
            api_key=GEMINI_API_KEY
        )


        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": str(prompt)
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


            try:
                data = response.json()

            except ValueError:
                data = {}


            # ------------------------------------------------
            # Successful Response
            # ------------------------------------------------

            if response.status_code == 200:

                candidates = data.get(
                    "candidates",
                    []
                )


                if not candidates:
                    last_error = (
                        f"{model}: Gemini returned no candidates."
                    )

                    continue


                content = candidates[0].get(
                    "content",
                    {}
                )


                parts = content.get(
                    "parts",
                    []
                )


                answer_parts = []


                for part in parts:

                    text = part.get(
                        "text"
                    )


                    if text:
                        answer_parts.append(
                            text
                        )


                answer = "\n".join(
                    answer_parts
                ).strip()


                if not answer:

                    last_error = (
                        f"{model}: Gemini returned "
                        "an empty answer."
                    )

                    continue


                # --------------------------------------------
                # Success
                # --------------------------------------------

                return {
                    "success": True,
                    "answer": answer,
                    "error": "",
                    "model": model
                }


            # ------------------------------------------------
            # API Key Error
            # ------------------------------------------------

            error_message = (
                data.get("error", {})
                .get(
                    "message",
                    "Gemini API request failed."
                )
            )


            error_text = str(
                error_message
            ).lower()


            # ------------------------------------------------
            # Invalid API Key
            # ------------------------------------------------

            if (
                "api key" in error_text
                or "api_key" in error_text
                or "authentication" in error_text
                or "unauthorized" in error_text
            ):

                return {
                    "success": False,
                    "answer": "",
                    "error": error_message
                }


            # ------------------------------------------------
            # Model / Quota / Temporary Failure
            # Try Next Model
            # ------------------------------------------------

            last_error = (
                f"{model}: {error_message}"
            )


            continue


        except requests.exceptions.Timeout:

            last_error = (
                f"{model}: Gemini API request timed out."
            )

            continue


        except requests.exceptions.RequestException as error:

            last_error = (
                f"{model}: {str(error)}"
            )

            continue


        except Exception as error:

            last_error = (
                f"{model}: {str(error)}"
            )

            continue


    # --------------------------------------------------------
    # All Models Failed
    # --------------------------------------------------------

    return {
        "success": False,
        "answer": "",
        "error": last_error
    }