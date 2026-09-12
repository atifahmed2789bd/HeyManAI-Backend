import os
import sqlite3
from datetime import datetime


# ============================================================
# HeyManAI Backend Memory
# ============================================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "heymanai_memory.db"
)


# ------------------------------------------------------------
# Database Connection
# ------------------------------------------------------------

def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH,
        timeout=30
    )

    connection.row_factory = sqlite3.Row

    return connection


# ------------------------------------------------------------
# Initialize Database
# ------------------------------------------------------------

def initialize_memory():
    connection = get_connection()

    try:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS conversation (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )

        connection.commit()

    finally:
        connection.close()


# ------------------------------------------------------------
# Save Message
# ------------------------------------------------------------

def save_message(role, content):
    if not content or not str(content).strip():
        return False

    connection = get_connection()

    try:
        connection.execute(
            """
            INSERT INTO conversation
            (role, content, created_at)
            VALUES (?, ?, ?)
            """,
            (
                str(role),
                str(content),
                datetime.utcnow().isoformat()
            )
        )

        connection.commit()

        return True

    finally:
        connection.close()


# ------------------------------------------------------------
# User Message
# ------------------------------------------------------------

def add_user_message(content):
    return save_message(
        "user",
        content
    )


# ------------------------------------------------------------
# Assistant Message
# ------------------------------------------------------------

def add_assistant_message(content):
    return save_message(
        "assistant",
        content
    )


# ------------------------------------------------------------
# Get All Memory
# ------------------------------------------------------------

def get_all_memory():
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                role,
                content,
                created_at
            FROM conversation
            ORDER BY id ASC
            """
        ).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


# ------------------------------------------------------------
# Get Recent Memory
# ------------------------------------------------------------

def get_recent_memory(limit=20):
    connection = get_connection()

    try:
        rows = connection.execute(
            """
            SELECT
                id,
                role,
                content,
                created_at
            FROM conversation
            ORDER BY id DESC
            LIMIT ?
            """,
            (int(limit),)
        ).fetchall()

        rows = list(reversed(rows))

        return [dict(row) for row in rows]

    finally:
        connection.close()


# ------------------------------------------------------------
# Get Relevant Memory
# ------------------------------------------------------------

def get_relevant_memory(query, max_results=12):
    if not query or not str(query).strip():
        return []

    keywords = extract_keywords(
        str(query)
    )

    if not keywords:
        return get_recent_memory(
            max_results
        )

    connection = get_connection()

    try:
        conditions = []
        parameters = []

        for keyword in keywords:
            conditions.append(
                "content LIKE ?"
            )

            parameters.append(
                f"%{keyword}%"
            )

        where_clause = " OR ".join(
            conditions
        )

        sql = f"""
            SELECT
                id,
                role,
                content,
                created_at
            FROM conversation
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT ?
        """

        parameters.append(
            int(max_results)
        )

        rows = connection.execute(
            sql,
            parameters
        ).fetchall()

        rows = list(reversed(rows))

        return [dict(row) for row in rows]

    finally:
        connection.close()


# ------------------------------------------------------------
# Keyword Extraction
# ------------------------------------------------------------

def extract_keywords(text):
    stop_words = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "am",
        "was",
        "were",
        "to",
        "of",
        "in",
        "on",
        "for",
        "and",
        "or",
        "but",
        "with",
        "this",
        "that",
        "what",
        "why",
        "how",
        "can",
        "could",
        "would",
        "should",
        "i",
        "you",
        "me",
        "my",
        "your",
        "we",
        "it",
        "do",
        "does",
        "did",

        "আমি",
        "আমার",
        "আমাকে",
        "তুমি",
        "তোমার",
        "তোমাকে",
        "কি",
        "কী",
        "কেন",
        "কিভাবে",
        "কীভাবে",
        "এই",
        "ওই",
        "এটা",
        "সেটা",
        "যে",
        "এবং",
        "বা",
        "এর",
        "তে",
        "থেকে",
        "জন্য",
        "হলে",
        "হয়",
        "হয়"
    }

    words = str(text).lower().split()

    keywords = []

    for word in words:
        cleaned = word.strip(
            ".,!?;:'\"()[]{}<>"
        )

        if not cleaned:
            continue

        if cleaned in stop_words:
            continue

        if len(cleaned) < 2:
            continue

        if cleaned not in keywords:
            keywords.append(cleaned)

    return keywords


# ------------------------------------------------------------
# Memory Text
# ------------------------------------------------------------

def get_memory_text(query=None, max_results=12):
    if query:
        memories = get_relevant_memory(
            query,
            max_results
        )
    else:
        memories = get_recent_memory(
            max_results
        )

    if not memories:
        return ""

    lines = []

    for memory in memories:
        role = memory.get(
            "role",
            ""
        )

        content = memory.get(
            "content",
            ""
        )

        if role == "user":
            label = "User"

        elif role == "assistant":
            label = "HeyManAI"

        else:
            label = role

        lines.append(
            f"{label}: {content}"
        )

    return "\n".join(lines)


# ------------------------------------------------------------
# Memory Count
# ------------------------------------------------------------

def get_memory_count():
    connection = get_connection()

    try:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total
            FROM conversation
            """
        ).fetchone()

        return int(
            row["total"]
        )

    finally:
        connection.close()


# ------------------------------------------------------------
# Clear Memory
# ------------------------------------------------------------

def clear_memory():
    connection = get_connection()

    try:
        connection.execute(
            "DELETE FROM conversation"
        )

        connection.commit()

        return True

    finally:
        connection.close()


# ------------------------------------------------------------
# Initialize Automatically
# ------------------------------------------------------------

initialize_memory()
