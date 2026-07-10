"""
database.py
-----------
Handles all SQLite database operations for the AI FAQ Chatbot.
Includes functions to manage FAQs and chat history.
"""

import sqlite3
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────
# Database file path
# ─────────────────────────────────────────────
DB_PATH = "faq_chatbot.db"


def get_connection():
    """Create and return a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # allows dict-like access to rows
    return conn


# ─────────────────────────────────────────────
# TABLE CREATION
# ─────────────────────────────────────────────

def create_tables():
    """Create the FAQs and chat history tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    # FAQs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            category TEXT DEFAULT 'General',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Chat history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_question TEXT NOT NULL,
            bot_answer TEXT NOT NULL,
            method_used TEXT NOT NULL,
            confidence_score REAL,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# FAQ OPERATIONS
# ─────────────────────────────────────────────

def insert_faq(question: str, answer: str, category: str = "General"):
    """Insert a single FAQ into the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)",
        (question.strip(), answer.strip(), category.strip())
    )
    conn.commit()
    conn.close()


def get_all_faqs() -> pd.DataFrame:
    """Fetch all FAQs and return as a Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query("SELECT * FROM faqs ORDER BY id ASC", conn)
    conn.close()
    return df


def update_faq(faq_id: int, question: str, answer: str, category: str):
    """Update an existing FAQ by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE faqs SET question=?, answer=?, category=? WHERE id=?",
        (question.strip(), answer.strip(), category.strip(), faq_id)
    )
    conn.commit()
    conn.close()


def delete_faq(faq_id: int):
    """Delete a FAQ by ID."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM faqs WHERE id=?", (faq_id,))
    conn.commit()
    conn.close()


def bulk_insert_faqs(df: pd.DataFrame):
    """
    Bulk insert FAQs from a Pandas DataFrame.
    Expected columns: 'question', 'answer', and optionally 'category'.
    """
    conn = get_connection()
    cursor = conn.cursor()

    inserted = 0
    skipped = 0

    for _, row in df.iterrows():
        try:
            question = str(row.get("question", "")).strip()
            answer = str(row.get("answer", "")).strip()
            category = str(row.get("category", "General")).strip()

            if question and answer:
                cursor.execute(
                    "INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)",
                    (question, answer, category)
                )
                inserted += 1
            else:
                skipped += 1
        except Exception:
            skipped += 1

    conn.commit()
    conn.close()
    return inserted, skipped


def get_faq_count() -> int:
    """Return total number of FAQs in the database."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM faqs")
    count = cursor.fetchone()[0]
    conn.close()
    return count


# ─────────────────────────────────────────────
# CHAT HISTORY OPERATIONS
# ─────────────────────────────────────────────

def save_chat(user_question: str, bot_answer: str, method_used: str, confidence_score: float):
    """Save a chat interaction to the database."""
    conn = get_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """INSERT INTO chat_history 
           (user_question, bot_answer, method_used, confidence_score, timestamp)
           VALUES (?, ?, ?, ?, ?)""",
        (user_question, bot_answer, method_used, round(confidence_score, 4), timestamp)
    )
    conn.commit()
    conn.close()


def get_chat_history() -> pd.DataFrame:
    """Fetch all chat history and return as a Pandas DataFrame."""
    conn = get_connection()
    df = pd.read_sql_query(
        "SELECT * FROM chat_history ORDER BY timestamp DESC", conn
    )
    conn.close()
    return df


def clear_chat_history():
    """Delete all records from the chat history table."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM chat_history")
    conn.commit()
    conn.close()


# ─────────────────────────────────────────────
# SEED PREDEFINED FAQs
# ─────────────────────────────────────────────

PREDEFINED_FAQS = [
    ("What is the admission process?",
     "The admission process involves submitting an online application, uploading required documents, paying the application fee, and attending an entrance exam or interview if required.",
     "Admission"),

    ("What documents are required for admission?",
     "You need to submit your 10th and 12th marksheets, transfer certificate, migration certificate, passport-size photographs, and a valid ID proof such as Aadhaar card.",
     "Documents"),

    ("What is the last date to apply?",
     "The last date to apply is generally announced on the official college website. For the current academic year, please check the admissions portal for the exact deadline.",
     "Admission"),

    ("Is there an entrance exam for admission?",
     "Yes, many programs require an entrance exam such as JEE, NEET, or a college-specific entrance test. The details vary by program.",
     "Exam"),

    ("What are the available courses?",
     "We offer undergraduate (B.Tech, BCA, BBA, B.Sc), postgraduate (M.Tech, MCA, MBA, M.Sc), and PhD programs across various departments.",
     "Courses"),

    ("What is the annual fee structure?",
     "The fee structure varies by program. Engineering programs typically range from ₹80,000 to ₹1,50,000 per year. Please visit the official website for the complete fee schedule.",
     "Fees"),

    ("Is hostel accommodation available?",
     "Yes, the college provides separate hostel facilities for boys and girls. Hostel admission is done on a first-come, first-served basis.",
     "Hostel"),

    ("Are scholarships available?",
     "Yes, we offer merit-based, need-based, and government scholarships. Students can apply through the scholarship portal after admission.",
     "Scholarship"),

    ("What is the eligibility criteria for B.Tech?",
     "For B.Tech admission, you must have passed 12th with Physics, Chemistry, and Mathematics with a minimum of 60% marks and a valid JEE score.",
     "Eligibility"),

    ("How can I contact the admissions office?",
     "You can contact the admissions office at admissions@college.edu or call +91-XXXXXXXXXX. Office hours are Monday to Saturday, 9 AM to 5 PM.",
     "Contact"),

    ("Is there a lateral entry option?",
     "Yes, lateral entry is available for diploma holders who wish to join the second year of B.Tech programs, subject to eligibility criteria.",
     "Admission"),

    ("What is the intake capacity for each course?",
     "The intake capacity varies by program. For example, B.Tech has 60 seats per branch, while BCA and BBA have 120 seats each.",
     "Courses"),

    ("Does the college have placement support?",
     "Yes, our Training and Placement Cell actively supports students with internships, career counseling, mock interviews, and campus recruitment drives.",
     "Placement"),

    ("What are the college timings?",
     "College operates from 8:30 AM to 4:30 PM, Monday to Saturday. Administrative offices are open till 5:00 PM.",
     "General"),

    ("Is there a sports or extracurricular program?",
     "Yes, the college has excellent sports facilities including a gym, basketball court, cricket ground, and also supports cultural clubs, tech clubs, and literary societies.",
     "General"),
]


def seed_predefined_faqs():
    """Insert predefined FAQs only if the database is empty."""
    if get_faq_count() == 0:
        conn = get_connection()
        cursor = conn.cursor()
        for question, answer, category in PREDEFINED_FAQS:
            cursor.execute(
                "INSERT INTO faqs (question, answer, category) VALUES (?, ?, ?)",
                (question, answer, category)
            )
        conn.commit()
        conn.close()
