import os


# ============================================================
# HeyManAI Backend Configuration
# ============================================================

# ------------------------------------------------------------
# API Server
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

DEBUG_MODE = os.getenv(
    "HEYMANAI_DEBUG",
    "false"
).lower() == "true"


# ------------------------------------------------------------
# Gemini AI
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
# HeyManAI Identity
# ------------------------------------------------------------

HEYMAN_NAME = "HeyMan"

USER_TITLE = "বস"


# ------------------------------------------------------------
# AI Settings
# ------------------------------------------------------------

AI_TEMPERATURE = 0.7

AI_MAX_OUTPUT_TOKENS = 2048

AI_TIMEOUT_SECONDS = 60


# ------------------------------------------------------------
# Memory System
# ------------------------------------------------------------

MEMORY_ENABLED = True

MEMORY_RELEVANT_RESULTS = 12


# ------------------------------------------------------------
# Voice System
# ------------------------------------------------------------

VOICE_INPUT_ENABLED = True

VOICE_OUTPUT_ENABLED = True


# ------------------------------------------------------------
# Assistant Systems
# ------------------------------------------------------------

TIME_ENABLED = True

DATE_ENABLED = True

DAY_ENABLED = True

WEATHER_ENABLED = True
