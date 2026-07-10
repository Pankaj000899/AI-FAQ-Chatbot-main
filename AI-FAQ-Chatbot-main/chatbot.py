"""
chatbot.py
----------
Core NLP engine for the AI FAQ Chatbot.
"""

import string
import numpy as np
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from database import get_all_faqs


CONFIDENCE_THRESHOLD = 0.25

FALLBACK_RESPONSE = (
    "I'm sorry, I couldn't find a confident answer to your question. "
    "Please try rephrasing it or contact the admissions office."
)


def download_nltk_resources():
    resources = ["punkt", "stopwords"]
    for resource in resources:
        try:
            nltk.download(resource, quiet=True)
        except Exception:
            pass


download_nltk_resources()


def preprocess_text(text: str) -> str:
    text = text.lower()
    text = text.translate(str.maketrans("", "", string.punctuation))

    try:
        tokens = word_tokenize(text)
    except Exception:
        tokens = text.split()

    try:
        stop_words = set(stopwords.words("english"))
    except Exception:
        stop_words = set()

    clean_tokens = []
    for word in tokens:
        if word not in stop_words and word.isalpha():
            clean_tokens.append(word)

    return " ".join(clean_tokens)


class TFIDFMatcher:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()
        self.faq_vectors = None
        self.faq_data = []

    def build_index(self, faqs: list):
        self.faq_data = faqs

        if not faqs:
            self.faq_vectors = None
            return

        questions = [preprocess_text(q) for q, _ in faqs]

        if not any(questions):
            self.faq_vectors = None
            return

        self.faq_vectors = self.vectorizer.fit_transform(questions)

    def find_best_match(self, user_query: str):
        if not self.faq_data or self.faq_vectors is None:
            return FALLBACK_RESPONSE, 0.0

        processed_query = preprocess_text(user_query)

        if not processed_query:
            return FALLBACK_RESPONSE, 0.0

        query_vector = self.vectorizer.transform([processed_query])
        similarities = cosine_similarity(query_vector, self.faq_vectors).flatten()

        best_idx = int(np.argmax(similarities))
        best_score = float(similarities[best_idx])

        if best_score < CONFIDENCE_THRESHOLD:
            return FALLBACK_RESPONSE, best_score

        return self.faq_data[best_idx][1], best_score


class SemanticMatcher:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = None
        self.faq_embeddings = None
        self.faq_data = []

    def load_model(self):
        if self.model is None:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(self.model_name)

    def build_index(self, faqs: list):
        self.faq_data = faqs
        self.faq_embeddings = None

    def find_best_match(self, user_query: str):
        if not self.faq_data:
            return FALLBACK_RESPONSE, 0.0

        try:
            self.load_model()

            questions = [q for q, _ in self.faq_data]

            if self.faq_embeddings is None:
                self.faq_embeddings = self.model.encode(
                    questions,
                    convert_to_numpy=True
                )

            query_embedding = self.model.encode(
                [user_query],
                convert_to_numpy=True
            )

            similarities = cosine_similarity(
                query_embedding,
                self.faq_embeddings
            ).flatten()

            best_idx = int(np.argmax(similarities))
            best_score = float(similarities[best_idx])

            if best_score < CONFIDENCE_THRESHOLD:
                return FALLBACK_RESPONSE, best_score

            return self.faq_data[best_idx][1], best_score

        except Exception as e:
            return (
                f"Semantic Search error: {str(e)}. Please use TF-IDF method.",
                0.0
            )


class ChatbotEngine:
    def __init__(self):
        self.tfidf_matcher = TFIDFMatcher()
        self.semantic_matcher = SemanticMatcher()
        self._faq_data = []
        self._loaded = False

    def load_faqs(self):
        try:
            df = get_all_faqs()
        except Exception:
            self._faq_data = []
            self._loaded = False
            return

        if df.empty:
            self._faq_data = []
            self._loaded = False
            return

        self._faq_data = list(zip(df["question"], df["answer"]))

        self.tfidf_matcher.build_index(self._faq_data)
        self.semantic_matcher.build_index(self._faq_data)

        self._loaded = True

    def get_response(self, user_query: str, method: str = "TF-IDF"):
        if not user_query.strip():
            return "Please enter a valid question.", 0.0, method

        if not self._loaded:
            self.load_faqs()

        if not self._faq_data:
            return (
                "No FAQs found in the database. Please add FAQs from Admin Panel.",
                0.0,
                method
            )

        if method == "Semantic Search":
            answer, score = self.semantic_matcher.find_best_match(user_query)
        else:
            answer, score = self.tfidf_matcher.find_best_match(user_query)

        return answer, score, method

    def reload(self):
        self._loaded = False
        self.load_faqs()


engine = ChatbotEngine()