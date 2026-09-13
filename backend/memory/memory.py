import sqlite3
import os
import re
from datetime import datetime


# ============================================================
# HeyManAI Persistent Memory
# ============================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATABASE_PATH = os.path.join(
    BASE_DIR,
    "heymanai_memory.db"
)


# ============================================================
# Database Connection
# ============================================================

def get_connection():

    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


# ============================================================
# Initialize Database
# ============================================================

def initialize_memory():
    """
    Memory database এবং conversation table তৈরি করে।

    গুরুত্বপূর্ণ:
    - কোনো automatic deletion নেই।
    - কোনো storage message limit নেই।
    - পুরোনো conversation নিজে থেকে মুছে যাবে না।
    """

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


# ============================================================
# Save Message
# ============================================================

def save_message(
    role,
    content
):
    """
    User অথবা assistant message permanent memory-তে save করে।

    কোনো fixed storage limit নেই।
    """

    if not isinstance(
        role,
        str
    ):
        return False

    if not isinstance(
        content,
        str
    ):
        return False

    role = role.strip()
    content = content.strip()

    if not role or not content:
        return False

    initialize_memory()

    connection = get_connection()

    try:

        connection.execute(
            """
            INSERT INTO conversation
            (
                role,
                content,
                created_at
            )
            VALUES (?, ?, ?)
            """,
            (
                role,
                content,
                datetime.now().isoformat(
                    timespec="seconds"
                )
            )
        )

        connection.commit()

        return True

    finally:

        connection.close()


# ============================================================
# Convenience Functions
# ============================================================

def add_user_message(
    content
):

    return save_message(
        "user",
        content
    )


def add_assistant_message(
    content
):

    return save_message(
        "assistant",
        content
    )


# ============================================================
# Relevant Memory
# ============================================================

def get_relevant_memory(
    query,
    max_results=12
):
    """
    বর্তমান প্রশ্নের সাথে সম্পর্কিত পুরোনো
    conversation খুঁজে বের করে।

    গুরুত্বপূর্ণ:
    max_results শুধুমাত্র AI-তে পাঠানো relevant
    memory-এর retrieval limit।

    এটি database storage limit নয়।
    পুরোনো message delete হয় না।
    """

    if not isinstance(
        query,
        str
    ):
        return ""

    query = query.strip()

    if not query:
        return ""

    initialize_memory()

    keywords = extract_keywords(
        query
    )

    if not keywords:
        return ""

    try:

        max_results = int(
            max_results
        )

    except (
        TypeError,
        ValueError
    ):

        max_results = 12

    if max_results < 1:
        max_results = 1

    connection = get_connection()

    try:

        conditions = []
        parameters = []

        for keyword in keywords:

            conditions.append(
                "LOWER(content) LIKE ?"
            )

            parameters.append(
                "%" + keyword.lower() + "%"
            )

        where_clause = " OR ".join(
            conditions
        )

        rows = connection.execute(
            f"""
            SELECT
                id,
                role,
                content,
                created_at
            FROM conversation
            WHERE {where_clause}
            ORDER BY id DESC
            LIMIT ?
            """,
            parameters + [
                max_results
            ]
        ).fetchall()

        if not rows:
            return ""

        rows = list(
            reversed(rows)
        )

        return format_memory_rows(
            rows
        )

    finally:

        connection.close()


# ============================================================
# Keyword Extraction
# ============================================================

def extract_keywords(
    text
):
    """
    Search-এর জন্য গুরুত্বপূর্ণ keyword বের করে।
    """

    if not isinstance(
        text,
        str
    ):
        return []

    words = re.findall(
        r"[A-Za-z0-9\u0980-\u09FF]+",
        text.lower()
    )

    stop_words = {
        "আমি",
        "আমার",
        "আমাকে",
        "তুমি",
        "তোমার",
        "তোমাকে",
        "এই",
        "ওই",
        "সেই",
        "কি",
        "কী",
        "কেন",
        "কিভাবে",
        "কীভাবে",
        "একটা",
        "একটি",
        "এবং",
        "আর",
        "এর",
        "তে",
        "কে",
        "না",
        "হয়",
        "হয়",
        "দাও",
        "করো",
        "করতে",

        "the",
        "a",
        "an",
        "and",
        "or",
        "is",
        "are",
        "am",
        "to",
        "of",
        "in",
        "on",
        "for",
        "with",
        "this",
        "that",
        "what",
        "why",
        "how",
        "my",
        "your",
        "you",
        "i"
    }

    keywords = []

    for word in words:

        if word in stop_words:
            continue

        if len(word) < 2:
            continue

        if word not in keywords:

            keywords.append(
                word
            )

    return keywords


# ============================================================
# Format Memory Rows
# ============================================================

def format_memory_rows(
    rows
):
    """
    Database rows-কে AI-readable memory text-এ
    convert করে।
    """

    if not rows:
        return ""

    result = []

    for row in rows:

        role = row["role"]

        if role == "user":

            role_name = "User"

        elif role == "assistant":

            role_name = "HeyManAI"

        else:

            role_name = role

        result.append(
            f"{role_name}: {row['content']}"
        )

    return "\n".join(
        result
    )


# ============================================================
# Get Complete Memory
# ============================================================

def get_all_memory_text():
    """
    সম্পূর্ণ conversation history ফেরত দেয়।

    কোনো fixed message-count limit নেই।
    কোনো automatic deletion নেই।

    এটি database-এর সম্পূর্ণ history।
    Gemini context limit আলাদা বিষয়।
    """

    initialize_memory()

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                role,
                content,
                created_at
            FROM conversation
            ORDER BY id ASC
            """
        ).fetchall()

        if not rows:
            return ""

        return format_memory_rows(
            rows
        )

    finally:

        connection.close()


# ============================================================
# Recent Memory
# ============================================================

def get_recent_memory(
    limit=12
):
    """
    সর্বশেষ কয়েকটি conversation entry ফেরত দেয়।

    গুরুত্বপূর্ণ:
    এটি storage limit নয়।

    Database-এর পুরোনো message মুছে যায় না।
    """

    initialize_memory()

    try:

        limit = int(
            limit
        )

    except (
        TypeError,
        ValueError
    ):

        limit = 12

    if limit < 1:
        limit = 1

    connection = get_connection()

    try:

        rows = connection.execute(
            """
            SELECT
                role,
                content,
                created_at
            FROM conversation
            ORDER BY id DESC
            LIMIT ?
            """,
            (
                limit,
            )
        ).fetchall()

        if not rows:
            return ""

        rows = list(
            reversed(rows)
        )

        return format_memory_rows(
            rows
        )

    finally:

        connection.close()


# ============================================================
# Memory Count
# ============================================================

def get_memory_count():
    """
    মোট conversation entry-এর সংখ্যা ফেরত দেয়।
    """

    initialize_memory()

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


# ============================================================
# Clear Memory
# ============================================================

def clear_memory():
    """
    শুধুমাত্র explicitভাবে call করলে
    সম্পূর্ণ conversation memory মুছে যাবে।

    কোনো automatic deletion নেই।
    """

    initialize_memory()

    connection = get_connection()

    try:

        connection.execute(
            """
            DELETE FROM conversation
            """
        )

        connection.commit()

    finally:

        connection.close()


# ============================================================
# Initialize On Import
# ============================================================

initialize_memory()