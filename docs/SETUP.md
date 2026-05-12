# Setup Guide

## Prerequisites

- Python 3.10+
- Supabase account (free tier works)
- Voyage AI API key
- Anthropic API key (Week 3+)

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
   - Run `scripts/sql/001_create_raw_schema.sql`

6. Load synthetic data:
   ```bash
   python scripts/load_synthea_patients.py
   ```

7. Verify connection:
   ```bash
   python scripts/test_connection.py
   ```
