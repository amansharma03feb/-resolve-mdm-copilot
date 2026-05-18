"""Bulk embed steward notes using Voyage AI voyage-3-lite (512-dim)."""

import os
import sys
import time
import psycopg2
import voyageai
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
VOYAGE_API_KEY = os.getenv("VOYAGE_API_KEY")
MODEL = "voyage-3-lite"
BATCH_SIZE = 5

if not DB_URL or not VOYAGE_API_KEY:
    print("ERROR: Set DATABASE_URL and VOYAGE_API_KEY in .env")
    sys.exit(1)

vo = voyageai.Client(api_key=VOYAGE_API_KEY)


def embed_batch(texts: list[str], retries: int = 5) -> list[list[float]]:
    for attempt in range(retries):
        try:
            result = vo.embed(texts, model=MODEL, input_type="document")
            return result.embeddings
        except Exception as e:
            if attempt < retries - 1:
                wait = 30 if "rate" in str(e).lower() else 2 ** (attempt + 1)
                print(f"    retry in {wait}s (attempt {attempt+1}/{retries})")
                time.sleep(wait)
            else:
                raise


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    cur.execute(
        "SELECT note_id, note FROM staging.steward_notes WHERE embedding IS NULL ORDER BY note_id"
    )
    rows = cur.fetchall()

    if not rows:
        print("All notes already have embeddings.")
        return

    print(f"Embedding {len(rows)} notes with {MODEL} in batches of {BATCH_SIZE}...")

    for i in range(0, len(rows), BATCH_SIZE):
        batch = rows[i : i + BATCH_SIZE]
        ids = [r[0] for r in batch]
        texts = [r[1] for r in batch]

        vectors = embed_batch(texts)

        for note_id, vec in zip(ids, vectors):
            cur.execute(
                "UPDATE staging.steward_notes SET embedding = %s WHERE note_id = %s",
                (str(vec), note_id),
            )

        conn.commit()
        print(f"  batch {i // BATCH_SIZE + 1}: embedded note_ids {ids[0]}-{ids[-1]} ({len(vec)} dims)")
        time.sleep(21)

    cur.close()
    conn.close()
    print("Done — all steward notes embedded.")


if __name__ == "__main__":
    main()
