import sqlite3
DB_NAME = "notes_app.db"
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
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

def save_quiz_result(user_id: int, topic: str, score:int, total: int):
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute(
        "INSERT INTO quizzes (user_id, topic, score, total_questions) VALUES (?, ?, ?, ?)",(user_id, topic, score, total)
    )
    conn.commit()
    conn.close()

def get_weak_topics(user_id: int):
    conn=sqlite3.connect(DB_NAME)
    cursor=conn.cursor()
    cursor.execute("""
    SELECT topic, (SUM(score) * 100.0/SUM(total_questions)) as accuracy
    FROM quizzes
    WHERE user_id= ?
    GROUP BY topic
    HAVING accuracy < 60.0
    """, (user_id,))
    weak_topics=[row[0] for row in cursor.fetchall()]
    conn.close()
    return weak_topics
    