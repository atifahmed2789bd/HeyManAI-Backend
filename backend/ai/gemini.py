import requests

from backend.config.config import (
    GEMINI_API_KEY,
    GEMINI_MODEL,
    GEMINI_API_URL,
    AI_TEMPERATURE,
    AI_MAX_OUTPUT_TOKENS,
    AI_TIMEOUT_SECONDS,
)


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
    3. Gemini API-তে request পাঠানো
    4. Large response support করা
    5. AI response cleanভাবে ফেরত দেওয়া

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

    try:

        prompt = build_prompt(
            message=message,
            memory=memory
        )

        url = (
            GEMINI_API_URL
            .replace(
                "{model}",
                GEMINI_MODEL
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

        if response.status_code != 200:

            return {
                "success": False,
                "error": (
                    "Gemini API error "
                    f"{response.status_code}: "
                    f"{response.text}"
                )
            }

        data = response.json()

        answer = extract_answer(
            data
        )

        if not answer:

            return {
                "success": False,
                "error": "Gemini returned an empty response."
            }

        return {
            "success": True,
            "answer": answer
        }

    except requests.exceptions.Timeout:

        return {
            "success": False,
            "error": "Gemini request timed out."
        }

    except requests.exceptions.RequestException as e:

        return {
            "success": False,
            "error": f"Network error: {str(e)}"
        }

    except Exception as e:

        return {
            "success": False,
            "error": f"Gemini error: {str(e)}"
        }


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

    if not isinstance(data, dict):
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