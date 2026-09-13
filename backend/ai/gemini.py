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
# FALLBACK SETTINGS
# ============================================================

# একটি model সাময়িকভাবে ব্যর্থ হলে একই model-এ
# সর্বোচ্চ কতবার পুনরায় চেষ্টা করা হবে।
MODEL_RETRY_COUNT = 2

# Retry-এর মাঝে অপেক্ষা।
RETRY_DELAY_SECONDS = 2


def ask_gemini(
    message,
    memory=None
):
    """
    ============================================================
    HeyManAI Gemini API Handler
    ============================================================

    দায়িত্ব:

    1. User message গ্রহণ করা
    2. Relevant memory যুক্ত করা
    3. সব configured Gemini model পরীক্ষা করা
    4. Model failure হলে পরের model-এ fallback করা
    5. Temporary error হলে retry করা
    6. Large response support করা
    7. সফল AI response ফেরত দেওয়া

    ============================================================
    """

    if not isinstance(message, str):
        return {
            "success": False,
            "error": "Message must be a string."
        }

    message = message.strip()

    if not message:
        return {
            "success": False,
            "error": "Message is empty."
        }

    if not GEMINI_API_KEY:
        return {
            "success": False,
            "error": "Gemini API key is not configured."
        }

    # ========================================================
    # MODEL LIST CHECK
    # ========================================================

    if not GEMINI_MODELS:

        return {
            "success": False,
            "error": "No Gemini models are configured."
        }

    # ========================================================
    # BUILD PROMPT
    # ========================================================

    try:

        prompt = build_prompt(
            message=message,
            memory=memory
        )

    except Exception as e:

        return {
            "success": False,
            "error": f"Prompt build error: {str(e)}"
        }

    # ========================================================
    # FALLBACK CHAIN
    # ========================================================

    errors = []

    for model in GEMINI_MODELS:

        if not isinstance(model, str):
            continue

        model = model.strip()

        if not model:
            continue

        # ----------------------------------------------------
        # একই model-এর জন্য retry
        # ----------------------------------------------------

        for attempt in range(
                1,
                MODEL_RETRY_COUNT + 1
        ):

            result = request_model(
                model=model,
                prompt=prompt
            )

            if result.get("success"):

                return {
                    "success": True,
                    "answer": result.get(
                        "answer",
                        ""
                    ),
                    "model": model
                }

            error = result.get(
                "error",
                "Unknown Gemini error."
            )

            status_code = result.get(
                "status_code"
            )

            errors.append(
                f"{model} "
                f"(attempt {attempt}): "
                f"{error}"
            )

            # ------------------------------------------------
            # Retryযোগ্য error হলে আবার চেষ্টা
            # ------------------------------------------------

            if is_retryable_error(
                    status_code
            ):

                if attempt < MODEL_RETRY_COUNT:

                    time.sleep(
                        RETRY_DELAY_SECONDS
                    )

                    continue

            # ------------------------------------------------
            # Retry করার দরকার নেই
            # পরের model-এ যাওয়া হবে
            # ------------------------------------------------

            break

    # ========================================================
    # ALL MODELS FAILED
    # ========================================================

    if errors:

        return {
            "success": False,
            "error": (
                "All configured Gemini models failed.\n"
                + "\n".join(errors)
            )
        }

    return {
        "success": False,
        "error": "No valid Gemini model was available."
    }


# ============================================================
# SINGLE MODEL REQUEST
# ============================================================

def request_model(
    model,
    prompt
):
    """
    একটি নির্দিষ্ট Gemini model-এ request পাঠায়।
    """

    try:

        url = (
            GEMINI_API_URL
            .replace(
                "{model}",
                model
            )
            .replace(
                "{api_key}",
                GEMINI_API_KEY
            )
        )

        payload = {
            "contents": [
                {
                    "role": "user",
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

        response = requests.post(
            url,
            json=payload,
            timeout=AI_TIMEOUT_SECONDS
        )

        status_code = response.status_code

        # ====================================================
        # SUCCESS
        # ====================================================

        if status_code == 200:

            try:

                data = response.json()

            except ValueError:

                return {
                    "success": False,
                    "status_code": status_code,
                    "error": (
                        "Gemini returned invalid JSON."
                    )
                }

            answer = extract_answer(
                data
            )

            if not answer:

                return {
                    "success": False,
                    "status_code": status_code,
                    "error": (
                        "Gemini returned an empty response."
                    )
                }

            return {
                "success": True,
                "answer": answer
            }

        # ====================================================
        # API ERROR
        # ====================================================

        return {
            "success": False,
            "status_code": status_code,
            "error": (
                f"Gemini API error "
                f"{status_code}: "
                f"{response.text}"
            )
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "status_code": 503,
            "error": "Gemini request timed out."
        }

    except requests.exceptions.ConnectionError as e:

        return {
            "success": False,
            "status_code": 503,
            "error": (
                f"Gemini connection error: {str(e)}"
            )
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "status_code": 503,
            "error": (
                f"Gemini network error: {str(e)}"
            )
        }

    except Exception as e:

        return {
            "success": False,
            "status_code": None,
            "error": f"Gemini error: {str(e)}"
        }


# ============================================================
# RETRYABLE ERROR CHECK
# ============================================================

def is_retryable_error(
    status_code
):
    """
    কোন error হলে একই model-এ retry করা হবে
    তা নির্ধারণ করে।
    """

    if status_code is None:
        return True

    # --------------------------------------------------------
    # 429 = Rate limit / Too many requests
    # --------------------------------------------------------

    if status_code == 429:
        return True

    # --------------------------------------------------------
    # 500-599 = Temporary server-side সমস্যা
    # --------------------------------------------------------

    if 500 <= status_code <= 599:
        return True

    return False


# ============================================================
# SYSTEM PROMPT
# ============================================================

def build_prompt(
    message,
    memory=None
):
    """
    ============================================================
    HeyManAI System Prompt
    ============================================================
    """

    prompt = (
        "তুমি HeyManAI। "
        "তোমার নাম HeyMan। "
        "তুমি একজন বুদ্ধিমান personal AI Assistant। "
        "ব্যবহারকারীকে সম্মানের সাথে 'বস' বলে সম্বোধন করবে। "
        "তোমার আচরণ বন্ধুসুলভ, caring এবং natural হবে। "
        "ব্যবহারকারীর ভাষা অনুসরণ করবে। "
        "বাংলায় প্রশ্ন করলে বাংলায় উত্তর দেবে। "
        "ইংরেজিতে প্রশ্ন করলে ইংরেজিতে উত্তর দিতে পারবে। "
        "প্রয়োজনে অন্য ভাষাতেও উত্তর দিতে পারবে। "
        "Romantic relationship বা romantic roleplay করবে না। "
        "নিশ্চিত না হলে পরিষ্কারভাবে জানাবে। "
    )

    prompt += (
        "\n\nVISUAL FORMATTING RULES:\n"
        "Markdown ব্যবহার করবে না। "
        "*, **, ***, #, ##, ### এবং ``` ব্যবহার করবে না। "
        "Bold-এর জন্য <b> অথবা <strong> ব্যবহার করতে পারো। "
        "Underline-এর জন্য <u> ব্যবহার করতে পারো। "
        "Italic-এর জন্য <i> অথবা <em> ব্যবহার করতে পারো। "
        "Highlight-এর জন্য <mark> ব্যবহার করতে পারো। "
        "Line break-এর জন্য <br> ব্যবহার করতে পারো। "
        "Unsafe HTML, CSS, JavaScript, <script>, <style> "
        "বা event handler ব্যবহার করবে না। "
    )

    prompt += (
        "\n\nCODING RULES:\n"
        "ব্যবহারকারী code চাইলে সম্পূর্ণ code "
        "শুধুমাত্র <pre><code>...</code></pre> "
        "এর ভিতরে থাকবে। "
        "Code-এর কোনো অংশ code block-এর বাইরে লিখবে না। "
        "একাধিক file হলে প্রতিটি file-এর code আলাদা "
        "<pre><code>...</code></pre> block-এ থাকবে। "
        "Markdown code fence ব্যবহার করবে না। "
        "Code-এর বাইরে শুধুমাত্র প্রয়োজনীয় explanation "
        "দেওয়া যাবে। "
    )

    prompt += (
        "\n\nLARGE RESPONSE RULES:\n"
        "প্রয়োজন হলে দীর্ঘ এবং বিস্তারিত উত্তর দিতে পারবে। "
        "অপ্রয়োজনীয়ভাবে উত্তর ছোট করবে না। "
        "ব্যবহারকারী দীর্ঘ code, document বা explanation চাইলে "
        "যতটা সম্ভব সম্পূর্ণ উত্তর দেবে। "
        "শুধু response ছোট রাখার জন্য গুরুত্বপূর্ণ অংশ বাদ দেবে না। "
        "তবে API-এর প্রকৃত model output limit অতিক্রম করার চেষ্টা করবে না। "
    )

    if memory:

        prompt += (
            "\n\nRELEVANT CONVERSATION MEMORY:\n"
        )

        prompt += str(
            memory
        )

    else:

        prompt += (
            "\n\nRELEVANT CONVERSATION MEMORY:\n"
            "কোনো relevant memory পাওয়া যায়নি।"
        )

    prompt += (
        "\n\nCURRENT USER MESSAGE:\n"
    )

    prompt += message

    prompt += (
        "\n\nবর্তমান প্রশ্নের সরাসরি, পরিষ্কার এবং "
        "প্রাসঙ্গিক উত্তর দাও।"
    )

    return prompt


# ============================================================
# RESPONSE EXTRACTOR
# ============================================================

def extract_answer(
    data
):
    """
    ============================================================
    Gemini Response Extractor
    ============================================================

    Gemini response-এর সব text parts সংগ্রহ করে
    একটি সম্পূর্ণ answer হিসেবে ফেরত দেয়।

    ============================================================
    """

    if not isinstance(
            data,
            dict
    ):
        return ""

    candidates = data.get(
        "candidates"
    )

    if not isinstance(
            candidates,
            list
    ):
        return ""

    texts = []

    for candidate in candidates:

        if not isinstance(
                candidate,
                dict
        ):
            continue

        content = candidate.get(
            "content"
        )

        if not isinstance(
                content,
                dict
        ):
            continue

        parts = content.get(
            "parts"
        )

        if not isinstance(
                parts,
                list
        ):
            continue

        for part in parts:

            if not isinstance(
                    part,
                    dict
            ):
                continue

            text = part.get(
                "text"
            )

            if isinstance(
                    text,
                    str
            ):

                text = text.strip()

                if text:
                    texts.append(
                        text
                    )

    if texts:

        return "\n".join(
            texts
        ).strip()

    return ""