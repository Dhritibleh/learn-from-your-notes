import json
import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parent.parent / "notes_app.db"

# A topic is considered weak when the latest performance for that topic
# is below this percentage.
WEAK_THRESHOLD = 40.0


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS materials(
        material_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        source_type TEXT NOT NULL,
        source_name TEXT,
        raw_text TEXT NOT NULL,
        subject TEXT NOT NULL,
        main_topic TEXT NOT NULL,
        summary TEXT NOT NULL,
        topics_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quiz_sets(
        quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
        material_id INTEGER NOT NULL,
        questions_json TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(material_id)
            REFERENCES materials(material_id)
            ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS attempts(
        attempt_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        material_id INTEGER NOT NULL,
        quiz_id INTEGER NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        percentage REAL NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(material_id)
            REFERENCES materials(material_id)
            ON DELETE CASCADE,
        FOREIGN KEY(quiz_id)
            REFERENCES quiz_sets(quiz_id)
            ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS question_results(
        result_id INTEGER PRIMARY KEY AUTOINCREMENT,
        attempt_id INTEGER NOT NULL,
        question_index INTEGER NOT NULL,
        topic TEXT NOT NULL,
        is_correct INTEGER NOT NULL,
        FOREIGN KEY(attempt_id)
            REFERENCES attempts(attempt_id)
            ON DELETE CASCADE
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS weak_topics(
        tracking_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL DEFAULT 1,
        material_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        active INTEGER NOT NULL DEFAULT 1,
        latest_percentage REAL NOT NULL,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, material_id, topic),
        FOREIGN KEY(material_id)
            REFERENCES materials(material_id)
            ON DELETE CASCADE
    )
    """)

    # Old table from the previous version.
    # Keeping it avoids breaking an existing notes_app.db.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS quizzes(
        quiz_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER DEFAULT 1,
        topic TEXT NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


def save_material(
    user_id: int,
    source_type: str,
    source_name: str,
    raw_text: str,
    subject: str,
    main_topic: str,
    summary: str,
    topics: list[dict]
) -> int:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO materials
        (
            user_id,
            source_type,
            source_name,
            raw_text,
            subject,
            main_topic,
            summary,
            topics_json
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            source_type,
            source_name,
            raw_text,
            subject,
            main_topic,
            summary,
            json.dumps(topics)
        )
    )

    material_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return int(material_id)


def get_material(material_id: int):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM materials
        WHERE material_id = ?
        """,
        (material_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return None

    data = dict(row)

    data["topics"] = json.loads(
        data["topics_json"]
    )

    return data


def save_quiz(
    material_id: int,
    questions: list[dict]
) -> int:

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO quiz_sets
        (material_id, questions_json)
        VALUES (?, ?)
        """,
        (
            material_id,
            json.dumps(questions)
        )
    )

    quiz_id = cursor.lastrowid

    conn.commit()
    conn.close()

    return int(quiz_id)


def get_quiz(quiz_id: int):

    conn = get_connection()

    row = conn.execute(
        """
        SELECT *
        FROM quiz_sets
        WHERE quiz_id = ?
        """,
        (quiz_id,)
    ).fetchone()

    conn.close()

    if row is None:
        return None

    data = dict(row)

    data["questions"] = json.loads(
        data["questions_json"]
    )

    return data


def get_recent_question_texts(
    material_id: int,
    limit_sets: int = 5
) -> list[str]:

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT questions_json
        FROM quiz_sets
        WHERE material_id = ?
        ORDER BY quiz_id DESC
        LIMIT ?
        """,
        (
            material_id,
            limit_sets
        )
    ).fetchall()

    conn.close()

    questions = []

    for row in rows:

        try:
            question_list = json.loads(
                row["questions_json"]
            )

        except json.JSONDecodeError:
            continue

        for question in question_list:

            text = question.get("question")

            if text:
                questions.append(text)

    return questions


def save_attempt_and_update_tracking(
    user_id: int,
    material_id: int,
    quiz_id: int,
    score: int,
    total_questions: int,
    question_results: list[dict]
) -> int:

    percentage = (
        score * 100.0 / total_questions
        if total_questions
        else 0.0
    )

    # Calculate performance separately for every topic
    topic_stats = {}

    for result in question_results:

        topic = result["topic"]

        if topic not in topic_stats:
            topic_stats[topic] = {
                "correct": 0,
                "total": 0
            }

        topic_stats[topic]["total"] += 1

        if result["is_correct"]:
            topic_stats[topic]["correct"] += 1

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        INSERT INTO attempts
        (
            user_id,
            material_id,
            quiz_id,
            score,
            total_questions,
            percentage
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            material_id,
            quiz_id,
            score,
            total_questions,
            percentage
        )
    )

    attempt_id = int(cursor.lastrowid)

    for index, result in enumerate(question_results):

        cursor.execute(
            """
            INSERT INTO question_results
            (
                attempt_id,
                question_index,
                topic,
                is_correct
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                attempt_id,
                index,
                result["topic"],
                1 if result["is_correct"] else 0
            )
        )

    # Update weak-topic tracking.
    #
    # Latest topic accuracy < 40%  -> keep tracking
    # Latest topic accuracy >= 40% -> stop tracking

    for topic, stats in topic_stats.items():

        topic_percentage = (
            stats["correct"] * 100.0 / stats["total"]
            if stats["total"]
            else 0.0
        )

        active = (
            1
            if topic_percentage < WEAK_THRESHOLD
            else 0
        )

        cursor.execute(
            """
            INSERT INTO weak_topics
            (
                user_id,
                material_id,
                topic,
                active,
                latest_percentage,
                updated_at
            )
            VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)

            ON CONFLICT(user_id, material_id, topic)

            DO UPDATE SET
                active = excluded.active,
                latest_percentage = excluded.latest_percentage,
                updated_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                material_id,
                topic,
                active,
                topic_percentage
            )
        )

    conn.commit()
    conn.close()

    return attempt_id


def get_active_weak_topics(
    user_id: int,
    material_id: int
) -> list[dict]:

    conn = get_connection()

    rows = conn.execute(
        """
        SELECT
            topic,
            latest_percentage
        FROM weak_topics
        WHERE
            user_id = ?
            AND material_id = ?
            AND active = 1
        ORDER BY
            latest_percentage ASC,
            topic ASC
        """,
        (
            user_id,
            material_id
        )
    ).fetchall()

    conn.close()

    return [
        dict(row)
        for row in rows
    ]