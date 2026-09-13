import os


# ============================================================
# SERVER
# ============================================================

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
    ).lower() == "true"
)


# ============================================================
# GEMINI API
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
)


# ============================================================
# GEMINI MODEL FALLBACK CHAIN
# ============================================================
#
# Model 1 ব্যর্থ হলে Model 2
# Model 2 ব্যর্থ হলে Model 3
# এভাবে সব model পরীক্ষা করা হবে।
#
# Render Environment Variable:
#
# GEMINI_MODELS=model1,model2,model3
#
# অথবা নিচের default list ব্যবহার হবে।
# ============================================================

_default_models = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
]


_model_environment = os.getenv(
    "GEMINI_MODELS",
    ""
).strip()


if _model_environment:

    GEMINI_MODELS = [
        model.strip()
        for model in _model_environment.split(",")
        if model.strip()
    ]

else:

    GEMINI_MODELS = _default_models


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================
#
# পুরোনো code যদি GEMINI_MODEL ব্যবহার করে,
# তাহলে প্রথম configured model ব্যবহার করবে।
# ============================================================

GEMINI_MODEL = (
    GEMINI_MODELS[0]
    if GEMINI_MODELS
    else ""
)


# ============================================================
# GEMINI API URL
# ============================================================

GEMINI_API_URL = (
    "https://generativelanguage.googleapis.com/"
    "v1beta/models/{model}:generateContent"
    "?key={api_key}"
)


# ============================================================
# AI GENERATION
# ============================================================

AI_TEMPERATURE = 0.7

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


# ============================================================
# LARGE RESPONSE
# ============================================================

LARGE_RESPONSE_ENABLED = True

MAX_RESPONSE_WORDS = 50000

TRUNCATE_LARGE_RESPONSES = False


# ============================================================
# MEMORY
# ============================================================

MEMORY_ENABLED = True

MEMORY_RELEVANT_RESULTS = 12


# ============================================================
# VOICE
# ============================================================

VOICE_INPUT_ENABLED = True

VOICE_OUTPUT_ENABLED = True


# ============================================================
# SYSTEM FEATURES
# ============================================================

TIME_ENABLED = True

DATE_ENABLED = True

DAY_ENABLED = True

WEATHER_ENABLED = True


# ============================================================
# HEYMANAI IDENTITY
# ============================================================

HEYMAN_NAME = "HeyMan"

USER_TITLE = "বস"