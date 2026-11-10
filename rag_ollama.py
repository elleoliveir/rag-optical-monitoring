import os
import glob
import json
import requests
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

DOCS_DIR = "docs"
EMB_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b")
TOP_K = 4


def load_texts():
    paths = glob.glob(os.path.join(DOCS_DIR, "**", "*.txt"), recursive=True)
    texts, metas = [], []
    for p in paths:
        with open(p, "r", encoding="utf-8") as f:
            t = f.read().strip()
        if t:
            texts.append(t)
            metas.append({"path": p})
    return texts, metas


def build_index(texts, embedder):
    embs = embedder.encode(texts, normalize_embeddings=True, show_progress_bar=True)
    embs = np.array(embs, dtype="float32")
    index = faiss.IndexFlatIP(embs.shape[1])  # cosine via inner product com normalize
    index.add(embs)
    return index


def retrieve(query, embedder, index, texts, metas, k=TOP_K):
    q = embedder.encode([query], normalize_embeddings=True)
    q = np.array(q, dtype="float32")
    scores, idxs = index.search(q, k)
    out = []
    for score, i in zip(scores[0], idxs[0]):
        out.append({"score": float(score), "text": texts[int(i)], "meta": metas[int(i)]})
    return out


def ollama_generate(prompt: str, model: str = OLLAMA_MODEL):
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=300,
    )
    r.raise_for_status()
    return r.json()["response"].strip()


def answer_no_rag(question: str):
    prompt = f"""You are a network monitoring assistant.
Answer the question as best as you can.

Question: {question}
"""
    return ollama_generate(prompt)


def answer_with_rag(question: str, retrieved):
    ctx = []
    for j, item in enumerate(retrieved, 1):
        ctx.append(f"[Doc {j} | score={item['score']:.3f} | {item['meta']['path']}]\n{item['text']}")
    context = "\n\n".join(ctx)

    prompt = f"""You are a network monitoring assistant.
Use ONLY the context below to answer. If the answer is not in the context, say you don't have enough evidence.

CONTEXT:
{context}

QUESTION:
{question}

Answer:
"""
    return ollama_generate(prompt)


def main():
    if not os.path.isdir(DOCS_DIR):
        raise FileNotFoundError(f"Pasta '{DOCS_DIR}' não existe. Gere os .txt em docs/ primeiro.")

    texts, metas = load_texts()
    print("Total de documentos carregados:", len(texts))
    if not texts:
        raise RuntimeError("Nenhum .txt encontrado em docs/.")

    embedder = SentenceTransformer(EMB_MODEL)
    index = build_index(texts, embedder)

    questions = [
        "Which amplifier is mainly responsible for the detected failures?",
        "During failure intervals, how does OSNR change at SPO2/18/11?",
        "Is there any device operating below normal optical power levels?",
        "Are there soft failures where the network is still operational?",
    ]

    results = []
    for q in questions:
        print("=" * 80)
        print("QUESTION:", q)

        print("\n--- WITHOUT RAG ---")
        ans0 = answer_no_rag(q)
        print(ans0)

        retrieved = retrieve(q, embedder, index, texts, metas, k=TOP_K)

        print("\n--- WITH RAG ---")
        ans1 = answer_with_rag(q, retrieved)
        print(ans1)

        results.append(
            {
                "question": q,
                "without_rag": ans0,
                "with_rag": ans1,
                "retrieved": [{"score": r["score"], "path": r["meta"]["path"]} for r in retrieved],
            }
        )

    with open("results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("\n✅ Salvei results.json (use isso no relatório).")


if __name__ == "__main__":
    main()