"""Embed steward notes using OpenAI text-embedding-3-small and store in pgvector."""

import os
import sys
import psycopg2
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

DB_URL = os.getenv("DATABASE_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = "text-embedding-3-small"

if not DB_URL or not OPENAI_API_KEY:
    print("ERROR: Set DATABASE_URL and OPENAI_API_KEY in .env")
    sys.exit(1)

client = OpenAI(api_key=OPENAI_API_KEY)


def get_embedding(text: str) -> list[float]:
    resp = client.embeddings.create(input=text, model=MODEL)
    return resp.data[0].embedding


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
