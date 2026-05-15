"""Embed steward notes using Voyage AI and store in pgvector."""

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


def get_embedding(text: str) -> list[float]:
    result = vo.embed([text], model=MODEL, input_type="document")
    return result.embeddings[0]


def main():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    cur.execute("SELECT note_id, note FROM staging.member_notes WHERE embedding IS NULL")
    rows = cur.fetchall()

    if not rows:
        print("All notes already have embeddings. Nothing to do.")
        return

    print(f"Embedding {len(rows)} notes with {MODEL}...")

    for note_id, note in rows:
        vec = get_embedding(note)
        cur.execute(
            "UPDATE staging.member_notes SET embedding = %s WHERE note_id = %s",
            (str(vec), note_id),
        )
        print(f"  note_id={note_id} embedded ({len(vec)} dims)")

    conn.commit()
    cur.close()
    conn.close()
    print("Done — all notes embedded.")


if __name__ == "__main__":
    main()
