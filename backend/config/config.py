import os


# ============================================================
# HeyManAI Backend Configuration
# ============================================================


# ------------------------------------------------------------
# Server
# ------------------------------------------------------------

API_HOST = os.getenv(
    "HEYMANAI_API_HOST",
    "0.0.0.0"
)

API_PORT = int(
    os.getenv(
        "HEYMANAI_API_PORT",
        "8000"
    )
)

DEBUG_MODE = (
    os.getenv(
        "HEYMANAI_DEBUG",
        "false"
    ).lower()
    == "true"
)


# ------------------------------------------------------------
# Gemini
# ------------------------------------------------------------

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
)

GEMINI_MODEL = os.getenv(
    "GEMINI_MODEL",
    "gemini-3.8-flash"
)

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/{model}:generateContent"
    "?key={api_key}"
)


# ------------------------------------------------------------
# HeyManAI
# ------------------------------------------------------------

HEYMAN_NAME = "HeyMan"

USER_TITLE = "বস"


# ------------------------------------------------------------
# AI Generation
# ------------------------------------------------------------

AI_TEMPERATURE = 0.7

# Large-response configuration.
# The UI is designed to display very large answers,
# but the actual Gemini API limit depends on the model.
AI_MAX_OUTPUT_TOKENS = int(
    os.getenv(
        "HEYMANAI_MAX_OUTPUT_TOKENS",
        "65536"
    )
)

AI_TIMEOUT_SECONDS = int(
    os.getenv(
        "HEYMANAI_AI_TIMEOUT",
        "120"
    )
)


# ------------------------------------------------------------
# Large Response Support
# ------------------------------------------------------------

LARGE_RESPONSE_ENABLED = True

# Target capacity for HeyManAI UI.
# This is a UI/content target, not a guarantee that Gemini
# will generate this many words in one API response.
MAX_RESPONSE_WORDS = 50000

# Do not truncate large AI responses in the backend.
TRUNCATE_LARGE_RESPONSES = False


# ------------------------------------------------------------
# Memory
# ------------------------------------------------------------

MEMORY_ENABLED = True

MEMORY_RELEVANT_RESULTS = 12


# ------------------------------------------------------------
# Voice
# ------------------------------------------------------------

VOICE_INPUT_ENABLED = True

VOICE_OUTPUT_ENABLED = True


# ------------------------------------------------------------
# System Features
# ------------------------------------------------------------

TIME_ENABLED = True

DATE_ENABLED = True

DAY_ENABLED = True

WEATHER_ENABLED = True