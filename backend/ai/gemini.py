import requests

from backend.config.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_API_URL,
    AI_TEMPERATURE,
    AI_MAX_OUTPUT_TOKENS,
    AI_TIMEOUT_SECONDS,
)


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

    url = GEMINI_API_URL.format(
        model=GEMINI_MODEL,
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

        data = response.json()

        if response.status_code != 200:
            error_message = (
                data.get("error", {})
                .get("message", "Gemini API request failed.")
            )

            return {
                "success": False,
                "answer": "",
                "error": error_message
            }

        candidates = data.get("candidates", [])

        if not candidates:
            return {
                "success": False,
                "answer": "",
                "error": "Gemini returned no candidates."
            }

        content = candidates[0].get("content", {})
        parts = content.get("parts", [])

        answer_parts = []

        for part in parts:
            text = part.get("text")

            if text:
                answer_parts.append(text)

        answer = "\n".join(answer_parts).strip()

        if not answer:
            return {
                "success": False,
                "answer": "",
                "error": "Gemini returned an empty answer."
            }

        return {
            "success": True,
            "answer": answer,
            "error": ""
        }

    except requests.exceptions.Timeout:
        return {
            "success": False,
            "answer": "",
            "error": "Gemini API request timed out."
        }

    except requests.exceptions.RequestException as error:
        return {
            "success": False,
            "answer": "",
            "error": str(error)
        }

    except Exception as error:
        return {
            "success": False,
            "answer": "",
            "error": str(error)
        }
