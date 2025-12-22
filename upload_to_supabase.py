#!/usr/bin/env python3
"""
Upload documents to Supabase automatically
Usage: python upload_to_supabase.py
"""

import os
from supabase import create_client, Client

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("ERROR: SUPABASE_URL and SUPABASE_KEY must be set in .env file")
    exit(1)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Read and parse the SQL file
import re

print("Reading documents_rows.sql...")
with open("documents_rows.sql", 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the INSERT values
match = re.match(r'INSERT INTO .+? VALUES\s+(.+)', content, re.DOTALL)
if not match:
    print("ERROR: Could not parse SQL file")
    exit(1)

values_part = match.group(1).strip()
if values_part.endswith(';'):
    values_part = values_part[:-1]

# Parse individual rows
print("Parsing rows...")
rows = []
current_row = ""
paren_count = 0
in_string = False
escape_next = False

for char in values_part:
    if escape_next:
        current_row += char
        escape_next = False
        continue

    if char == '\\':
        escape_next = True
        current_row += char
        continue

    if char == "'" and not in_string:
        in_string = True
    elif char == "'" and in_string:
        in_string = False

    if not in_string:
        if char == '(':
            paren_count += 1
        elif char == ')':
            paren_count -= 1

    current_row += char

    if not in_string and paren_count == 0 and current_row.strip():
        row = current_row.strip()
        if row.endswith(','):
            row = row[:-1]
        if row:
            rows.append(row)
        current_row = ""

print(f"Found {len(rows)} rows")

# Parse each row into a dictionary
print("Converting to dictionaries...")
import json

documents = []
for i, row in enumerate(rows):
    # Remove outer parentheses
    row = row.strip()
    if row.startswith('(') and row.endswith(')'):
        row = row[1:-1]

    # Split by comma (but not inside quotes or brackets)
    parts = []
    current = ""
    in_quotes = False
    in_brackets = 0
    escape = False

    for char in row:
        if escape:
            current += char
            escape = False
            continue

        if char == '\\':
            escape = True
            current += char
            continue

        if char == "'" and in_brackets == 0:
            in_quotes = not in_quotes
            current += char
        elif char == '[' and not in_quotes:
            in_brackets += 1
            current += char
        elif char == ']' and not in_quotes:
            in_brackets -= 1
            current += char
        elif char == ',' and not in_quotes and in_brackets == 0:
            parts.append(current.strip())
            current = ""
        else:
            current += char

    if current:
        parts.append(current.strip())

    if len(parts) >= 5:
        # Remove quotes from string values
        def unquote(s):
            s = s.strip()
            if s.startswith("'") and s.endswith("'"):
                return s[1:-1]
            return s

        doc_id = unquote(parts[0])
        content_text = unquote(parts[1])
        embedding_str = unquote(parts[2])
        metadata_str = unquote(parts[3])
        ingestion_date = unquote(parts[4])

        # Parse embedding JSON array
        embedding = json.loads(embedding_str)

        # Parse metadata JSON
        metadata = json.loads(metadata_str)

        doc = {
            "id": int(doc_id),
            "content": content_text,
            "embedding": embedding,
            "metadata": metadata,
            "ingestion_date": ingestion_date
        }
        documents.append(doc)

        if (i + 1) % 10 == 0:
            print(f"  Processed {i + 1}/{len(rows)} rows...")

print(f"\nUploading {len(documents)} documents to Supabase...")

# Upload in batches
BATCH_SIZE = 10
total = len(documents)
uploaded = 0
errors = 0

for i in range(0, total, BATCH_SIZE):
    batch = documents[i:i + BATCH_SIZE]
    try:
        result = supabase.table("documents").insert(batch).execute()
        uploaded += len(batch)
        print(f"  Uploaded batch {i//BATCH_SIZE + 1}: {uploaded}/{total} documents")
    except Exception as e:
        errors += len(batch)
        print(f"  ERROR in batch {i//BATCH_SIZE + 1}: {e}")

print(f"\n{'='*50}")
print(f"Upload complete!")
print(f"  Successfully uploaded: {uploaded} documents")
if errors > 0:
    print(f"  Errors: {errors} documents")
print(f"{'='*50}")
