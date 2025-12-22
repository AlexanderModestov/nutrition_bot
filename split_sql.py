#!/usr/bin/env python3
"""Split a large INSERT statement into smaller batches"""

import os
import re

# Configuration
INPUT_FILE = "documents_rows.sql"
OUTPUT_DIR = "sql_batches"
ROWS_PER_BATCH = 10  # Split into smaller batches for SQL Editor

# Read the entire file
with open(INPUT_FILE, 'r', encoding='utf-8') as f:
    content = f.read()

# Extract the INSERT header and values
match = re.match(r'(INSERT INTO .+? VALUES\s+)(.+)', content, re.DOTALL)
if not match:
    print("ERROR: Could not parse SQL file")
    exit(1)

insert_header = match.group(1).strip()
values_part = match.group(2).strip()

# Remove the trailing semicolon if present
if values_part.endswith(';'):
    values_part = values_part[:-1]

# Split into individual value rows
# Each row starts with '(' and ends with '),'  or ')' for the last one
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

    # When we close a complete row
    if not in_string and paren_count == 0 and current_row.strip():
        # Remove trailing comma and whitespace
        row = current_row.strip()
        if row.endswith(','):
            row = row[:-1]
        if row:
            rows.append(row)
        current_row = ""

print(f"Found {len(rows)} rows in the SQL file")

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Split into batches
batch_num = 1
for i in range(0, len(rows), ROWS_PER_BATCH):
    batch_rows = rows[i:i + ROWS_PER_BATCH]

    # Create the batch SQL
    batch_sql = insert_header + "\n"
    batch_sql += ",\n".join(batch_rows)
    batch_sql += ";"

    # Write to file
    output_file = os.path.join(OUTPUT_DIR, f"documents_batch_{batch_num}.sql")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(batch_sql)

    print(f"Created batch {batch_num}: {len(batch_rows)} rows -> {output_file}")
    batch_num += 1

print(f"\nDone! Created {batch_num - 1} batch files in {OUTPUT_DIR}/")
