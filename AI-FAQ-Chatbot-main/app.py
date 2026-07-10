import streamlit as st
import sqlite3
import pandas as pd
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DB_NAME = "faq_chatbot.db"

faqs = [
    ("What is the admission process?", "You can apply online through the college admission portal."),
    ("What courses are available?", "We offer B.Tech, MBA, MCA, BBA, and Diploma courses."),
    ("What is the fee structure?", "The fee depends on the course. Please contact the admission office."),
    ("Is hostel facility available?", "Yes, hostel facilities are available for boys and girls."),
    ("Is scholarship available?", "Yes, scholarships are available based on merit and government schemes."),
    ("What documents are required?", "You need marksheets, ID proof, photos, and category certificate if applicable."),
]

def create_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS faqs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT
        )
    """)

    c.execute("SELECT COUNT(*) FROM faqs")
    if c.fetchone()[0] == 0:
        c.executemany("INSERT INTO faqs (question, answer) VALUES (?, ?)", faqs)

    conn.commit()
    conn.close()

def get_faqs():
    conn = sqlite3.connect(DB_NAME)
    df = pd.read_sql_query("SELECT * FROM faqs", conn)
    conn.close()
    return df

def add_faq(question, answer):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT INTO faqs (question, answer) VALUES (?, ?)", (question, answer))
    conn.commit()
    conn.close()

def delete_faq(faq_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("DELETE FROM faqs WHERE id=?", (faq_id,))
    conn.commit()
    conn.close()

def clean_text(text):
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))
    return text

def get_answer(user_question):
    df = get_faqs()

    if df.empty:
        return "No FAQs available.", 0

    questions = df["question"].apply(clean_text).tolist()
    user_question_clean = clean_text(user_question)

    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(questions + [user_question_clean])

    similarity = cosine_similarity(vectors[-1], vectors[:-1]).flatten()
    best_index = similarity.argmax()
    score = similarity[best_index]

    if score < 0.2:
        return "Sorry, I could not understand your question. Please try again.", score

    return df.iloc[best_index]["answer"], score

create_db()

st.set_page_config(page_title="AI FAQ Chatbot", page_icon="🎓")

st.title("🎓 AI FAQ Chatbot")
st.write("College Admission FAQ Chatbot using NLP and Cosine Similarity")

menu = st.sidebar.radio("Menu", ["Chatbot", "Admin Panel", "View FAQs"])

if menu == "Chatbot":
    st.subheader("💬 Ask your question")

    user_question = st.text_input("Enter your question")

    if st.button("Ask"):
        if user_question.strip():
            answer, score = get_answer(user_question)
            st.success(answer)
            st.info(f"Confidence Score: {score:.2f}")
        else:
            st.warning("Please enter a question.")

elif menu == "Admin Panel":
    st.subheader("🛠 Add New FAQ")

    question = st.text_area("Question")
    answer = st.text_area("Answer")

    if st.button("Add FAQ"):
        if question.strip() and answer.strip():
            add_faq(question, answer)
            st.success("FAQ added successfully!")
        else:
            st.warning("Both fields are required.")

    st.subheader("🗑 Delete FAQ")
    df = get_faqs()
    st.dataframe(df)

    faq_id = st.number_input("Enter FAQ ID to delete", min_value=1, step=1)

    if st.button("Delete"):
        delete_faq(faq_id)
        st.success("FAQ deleted successfully!")
        st.rerun()

elif menu == "View FAQs":
    st.subheader("📋 All FAQs")
    df = get_faqs()
    st.dataframe(df)