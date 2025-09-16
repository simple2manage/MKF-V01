import os
import json
import pathlib
import requests
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer
from django.conf import settings

DATA_FILE = settings.RAG_DATA_FILE
INDEX_DIR = pathlib.Path(settings.FAISS_INDEX_DIR)
INDEX_FILE = settings.INDEX_FILE
META_FILE = settings.META_FILE
INDEX_PATH = INDEX_DIR / INDEX_FILE
META_PATH = INDEX_DIR / META_FILE

EMBED_MODEL_NAME = "all-MiniLM-L6-v2"
OPENROUTER_MODEL = settings.OPENROUTER_MODEL
OPENROUTER_API_KEY = settings.OPENROUTER_API_KEY
OPENROUTER_API_URL = settings.OPENROUTER_API_URL

_embedder = SentenceTransformer(EMBED_MODEL_NAME)

def _load_corpus():
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def _ensure_index():
    INDEX_DIR.mkdir(parents=True, exist_ok=True)
    if INDEX_PATH.exists() and META_PATH.exists():
        index = faiss.read_index(str(INDEX_PATH))
        with open(META_PATH, "r", encoding="utf-8") as f:
            corpus = json.load(f)
        return index, corpus

    corpus = _load_corpus()
    vecs = _embedder.encode(corpus, convert_to_numpy=True, show_progress_bar=False).astype(np.float32)
    faiss.normalize_L2(vecs)
    index = faiss.IndexFlatIP(vecs.shape[1])
    index.add(vecs)
    faiss.write_index(index, str(INDEX_PATH))
    with open(META_PATH, "w", encoding="utf-8") as f:
        json.dump(corpus, f, ensure_ascii=False, indent=2)
    return index, corpus

_index, _corpus = _ensure_index()

def retrieve(query: str, k: int = 4):
    qv = _embedder.encode([query], convert_to_numpy=True).astype(np.float32)
    faiss.normalize_L2(qv)
    scores, idxs = _index.search(qv, k)
    idxs = idxs[0].tolist()
    ctx = [_corpus[i] for i in idxs if 0 <= i < len(_corpus)]
    return ctx

def llm_answer(prompt: str) -> str:
    if not OPENROUTER_API_KEY:
        return "LLM not configured."
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}"
        }
        payload = {
            "model": OPENROUTER_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.2,
            "max_tokens": 600
        }
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        choices = data.get("choices", [])
        if choices and "message" in choices[0]:
            return choices[0]["message"].get("content", "").strip()
        return "No answer returned from the model."
    except Exception as e:
        return f"Error: {str(e)}"

def answer(user_question: str) -> str:
    ctx = retrieve(user_question, k=5)
    prompt = (
        "Answer the question strictly using the provided context. "
        "If unsure, say you don’t know.\n\n"
        f"Context:\n- " + "\n- ".join(ctx) + "\n\n"
        f"Question: {user_question}\nAnswer:"
    )
    return llm_answer(prompt)
