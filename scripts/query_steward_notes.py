"""Semantic search over steward notes — find similar past decisions."""

import os
import sys
import psycopg2
import voyageai
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
MODEL = "voyage-3-lite"

if not DB_URL or not VOYAGE_API_KEY:
    print("ERROR: Set DATABASE_URL and VOYAGE_API_KEY in .env")
    sys.exit(1)

vo = voyageai.Client(api_key=VOYAGE_API_KEY)

QUERY = (
    sys.argv[1]
    if len(sys.argv) > 1
    else "SSN digits are transposed but name and DOB match exactly"
)


def main():
    query_vec = vo.embed([QUERY], model=MODEL, input_type="query").embeddings[0]

    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    cur.execute(
        """
        SELECT note_id, steward, action, confidence,
               note,
               1 - (embedding <=> %s::vector) AS similarity
        FROM staging.steward_notes
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT 3
        """,
        (str(query_vec), str(query_vec)),
    )

    results = cur.fetchall()
    print(f'\nQuery: "{QUERY}"\n')
    print("-" * 80)
    for note_id, steward, action, conf, note, sim in results:
        print(f"[{action}] similarity={sim:.4f}  confidence={conf}  steward={steward}")
        print(f"  {note[:150]}")
        print()

    cur.close()
    conn.close()


if __name__ == "__main__":
    main()
