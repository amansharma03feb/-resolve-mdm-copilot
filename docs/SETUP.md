# Setup Guide — Verify

## Prerequisites

- Python 3.10+
- Supabase account (free tier works)
- Voyage AI API key
- Anthropic API key (Week 3+)
- LangSmith API key (observability)

## Quick Start

1. Clone the repo:
   ```bash
   git clone https://github.com/amansharma03feb/-resolve-mdm-copilot.git
   cd resolve-mdm-copilot
   ```

2. Create virtual environment:
   ```bash
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Configure environment:
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. Create the database schema:
   - Open Supabase SQL Editor
   - Run scripts in order: `scripts/sql/001_create_raw_schema.sql` through `012`

6. Load synthetic data:
   ```bash
   python scripts/load_synthea_patients.py
   ```

7. Embed reviewer notes:
   ```bash
   python scripts/embed_reviewer_notes.py
   ```

8. Launch the dashboard:
   ```bash
   python -m streamlit run app/streamlit_app.py
   ```

9. Verify connection:
   ```bash
   python scripts/test_connection.py
   ```
