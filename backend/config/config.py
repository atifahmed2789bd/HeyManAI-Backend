import os


# ============================================================
# HeyManAI Backend Configuration
# ============================================================
#
# এই ফাইলের দায়িত্ব:
#
# 1. Server configuration
# 2. Gemini API configuration
# 3. Gemini model fallback configuration
# 4. AI generation configuration
# 5. Large response configuration
# 6. Memory configuration
# 7. Feature configuration
#
# AI personality / behavior এখানে থাকবে না।
# Personality / behavior AnswerBuilder.java থেকে আসবে।
#
# ============================================================


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
    ).strip().lower() == "true"
)


# ============================================================
# GEMINI API
# ============================================================

GEMINI_API_KEY = os.getenv(
    "GEMINI_API_KEY",
    ""
).strip()


# ============================================================
# GEMINI MODEL FALLBACK CHAIN
# ============================================================
#
# Render Environment Variable:
#
# GEMINI_MODELS=model1,model2,model3
#
# উদাহরণ:
#
# GEMINI_MODELS=gemini-3.8-flash,gemini-3.7-flash
#
# Environment variable না থাকলে নিচের default models
# ব্যবহার করা হবে।
#
# প্রথম model ব্যর্থ হলে পরের model পরীক্ষা করা হবে।
#
# ============================================================

DEFAULT_GEMINI_MODELS = [
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

    GEMINI_MODELS = DEFAULT_GEMINI_MODELS.copy()


# ============================================================
# BACKWARD COMPATIBILITY
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

AI_TEMPERATURE = float(
    os.getenv(
        "HEYMANAI_TEMPERATURE",
        "0.7"
    )
)


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


# ------------------------------------------------------------
# এই সংখ্যা storage limit নয়।
#
# এটি শুধুমাত্র relevant memory retrieval-এর default
# result count হিসেবে ব্যবহার করা যেতে পারে।
#
# পুরোনো conversation automatically delete হবে না।
# ------------------------------------------------------------

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
#
# এগুলো configuration-level identity values।
# Detailed behavior AnswerBuilder.java-তে থাকবে।
#
# ============================================================

HEYMAN_NAME = "HeyMan"


USER_TITLE = "বস"
