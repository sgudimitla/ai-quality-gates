"""SafeBank FAQ bot: a tiny RAG app (search the docs, then ask the AI)."""
import os
import re
import sys

from dotenv import load_dotenv
from google import genai
from langsmith import traceable

load_dotenv()  # reads GOOGLE_API_KEY and LANGSMITH_* from your .env file

MODEL = "gemini-3.5-flash-lite"  # change here if you switch models

# --- 1. The knowledge base (same 8 chunks as Topic 7) ---
DOCS = {
    "D1": "Savings account minimum balance is ₹5,000. Fee if below: ₹250/month.",
    "D2": "Salary accounts have zero minimum balance.",
    "D3": "ATM: 5 free withdrawals per month. ₹21 per extra withdrawal.",
    "D4": "International ATM withdrawals: ₹150 per withdrawal plus 3.5% currency markup.",
    "D5": "Fixed deposit (1 year): 7.0%. Senior citizens get +0.5%.",
    "D6": "Premature FD withdrawal penalty: 1%.",
    "D7": "Lost card: block via app or call 1800-000-1234.",
    "D8": "Branch hours: Mon–Sat, 10am–4pm. Closed 2nd and 4th Saturdays.",
}

STOPWORDS = {"i", "a", "an", "the", "is", "my", "me", "what", "whats", "s", "do",
             "does", "have", "how", "much", "for", "of", "in", "to", "on", "it", "and"}


def words(text):
    """Lowercase words, minus filler words."""
    return {w for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOPWORDS}


# --- 2. Search: score each chunk by how many words it shares with the question ---
@traceable(run_type="retriever")
def retrieve(question, k=2):
    q = words(question)
    scored = [(len(q & words(text)), doc_id, text) for doc_id, text in DOCS.items()]
    scored.sort(key=lambda s: s[0], reverse=True)
    return [(doc_id, text) for score, doc_id, text in scored[:k] if score > 0]


PROMPT = """Answer ONLY using the documents below.
Use common sense to connect the question to the documents (for example, a city in another country means "international").
If the documents only partly answer the question, answer what you can and say what is missing.
If the documents do not answer the question at all, say "I don't know".
Write plain text only, with no markdown and no document IDs.
If the customer states something the documents contradict, politely correct it.
You cannot access accounts, issue refunds or perform actions; say so when asked.
Documents:
{docs}
Question: {question}"""


# --- 3. Answer: send the found chunks + question to the AI ---
@traceable(run_type="llm")
def generate(prompt):
    client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
    response = client.models.generate_content(model=MODEL, contents=prompt)
    return response.text.strip()


@traceable(name="SafeBank answer")
def answer(question, k=2):
    chunks = retrieve(question, k)
    docs = "\n".join(f"{doc_id}: {text}" for doc_id, text in chunks) or "(no documents found)"
    return {
        "answer": generate(PROMPT.format(docs=docs, question=question)),
        "chunk_ids": [doc_id for doc_id, _ in chunks],
        "context": [text for _, text in chunks],
    }


if __name__ == "__main__":
    question = " ".join(sys.argv[1:]) or "What's the minimum balance for a savings account?"
    result = answer(question)
    print("Question :", question)
    print("Retrieved:", result["chunk_ids"])
    print("Answer   :", result["answer"])

    from langsmith import Client
    Client().flush()  # upload traces before the script exits