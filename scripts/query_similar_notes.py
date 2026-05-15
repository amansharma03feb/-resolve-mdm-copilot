"""Semantic search over steward notes — find similar resolution notes for a query."""

import os
import sys
import psycopg2
import voyageai
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
MODEL = os.getenv("EMBEDDING_MODEL", "voyage-3")

if not DB_URL or not VOYAGE_API_KEY:
    print("ERROR: Set DATABASE_URL and VOYAGE_API_KEY in .env")
    sys.exit(1)

vo = voyageai.Client(api_key=VOYAGE_API_KEY)

QUERY = (
    sys.argv[1] if len(sys.argv) > 1
    else "member with name spelling difference due to legacy system migration"
)


def get_embedding(text: str) -> list[float]:
    result = vo.embed([text], model=MODEL, input_type="query")
    return result.embeddings[0]


def main():
    query_vec = get_embedding(QUERY)

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT note_id, steward, action, confidence,
               note,
               embedding <=> %s::vector AS distance
        FROM staging.member_notes
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT 3
        """,
        (str(query_vec), str(query_vec)),
    )

    results = cur.fetchall()
    print(f"\nQuery: \"{QUERY}\"\n")
    print("-" * 80)
    for note_id, steward, action, conf, note, dist in results:
        print(f"[{action}] confidence={conf}  distance={dist:.4f}  steward={steward}")
        print(f"  {note[:120]}...")
        print()

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
