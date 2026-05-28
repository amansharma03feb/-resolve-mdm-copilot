"""Test LangSmith tracing with a Voyage AI embedding call.

Verifies that:
1. LANGSMITH_API_KEY is configured
2. Tracing is enabled (LANGCHAIN_TRACING_V2=true)
3. A traced embedding call appears in LangSmith dashboard
"""

import os
import time

import voyageai
from dotenv import load_dotenv
from langsmith import Client, traceable

load_dotenv()

VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")

os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")
os.environ.setdefault("LANGCHAIN_PROJECT", "verify-ai-copilot")

if not VOYAGE_API_KEY:
    raise SystemExit("ERROR: Set VOYAGE_API_KEY in .env")
if not LANGSMITH_API_KEY:
    raise SystemExit("ERROR: Set LANGSMITH_API_KEY in .env")

vo = voyageai.Client(api_key=VOYAGE_API_KEY)
ls = Client()


@traceable(name="embed_steward_note", run_type="embedding")
def embed_text(text: str) -> list[float]:
    result = vo.embed([text], model="voyage-3-lite", input_type="document")
    return result.embeddings[0]


@traceable(name="similarity_search_test", run_type="chain")
def similarity_test():
    note = "Same DOB, SSN last4 match, first name differs — Robert vs Bob. Merged as common nickname."
    query = "SSN digits transposed but name and DOB match exactly"

    print("Embedding steward note...")
    note_vec = embed_text(note)
    print(f"  -> {len(note_vec)} dimensions")

    time.sleep(21)

    print("Embedding search query...")
    query_vec = embed_text(query)
    print(f"  -> {len(query_vec)} dimensions")

    dot = sum(a * b for a, b in zip(note_vec, query_vec))
    norm_a = sum(a * a for a in note_vec) ** 0.5
    norm_b = sum(b * b for b in query_vec) ** 0.5
    cosine_sim = dot / (norm_a * norm_b)

    print(f"\nCosine similarity: {cosine_sim:.4f}")
    return {"note_dims": len(note_vec), "query_dims": len(query_vec), "cosine_similarity": cosine_sim}


def main():
    print("Testing LangSmith tracing...")
    print(f"  Project: {os.getenv('LANGCHAIN_PROJECT', 'default')}")
    print(f"  Tracing: {os.getenv('LANGCHAIN_TRACING_V2', 'false')}")
    print()

    result = similarity_test()

    print(f"\nDone. Check LangSmith dashboard for traced runs.")
    print(f"  https://smith.langchain.com/")


if __name__ == "__main__":
    main()
