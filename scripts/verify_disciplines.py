"""
Verify and ensure disciplines.csv aligns cleanly with STARTER_DISCIPLINES in database.py.
"""
import sys
import os
import csv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import database

csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'disciplines.csv')

with open(csv_path, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)

csv_disciplines = []
for r in rows:
    d = r['Discipline'].strip()
    if d not in csv_disciplines:
        csv_disciplines.append(d)

db_disciplines = list(database.STARTER_DISCIPLINES)

print("DB Starter Disciplines:", db_disciplines)
print("CSV Disciplines:", csv_disciplines)

missing_in_csv = [d for d in db_disciplines if d not in csv_disciplines]
extra_in_csv = [d for d in csv_disciplines if d not in db_disciplines]

print("Missing in CSV:", missing_in_csv)
print("Extra in CSV:", extra_in_csv)

# Ensure canonical order matching DB STARTER_DISCIPLINES
disciplines_data = {}
for r in rows:
    d = r['Discipline'].strip()
    if d not in disciplines_data:
        disciplines_data[d] = []
    disciplines_data[d].append((r['Subject'].strip(), r['Topic'].strip()))

# Re-write disciplines.csv in canonical order matching database.py STARTER_DISCIPLINES
out_rows = []
for d in db_disciplines:
    if d in disciplines_data:
        for subj, top in disciplines_data[d]:
            out_rows.append({'Discipline': d, 'Subject': subj, 'Topic': top})

# Save clean disciplines.csv
with open(csv_path, 'w', encoding='utf-8', newline='') as f:
    writer = csv.DictWriter(f, fieldnames=['Discipline', 'Subject', 'Topic'])
    writer.writeheader()
    writer.writerows(out_rows)

print(f"Successfully re-formatted and verified {csv_path} with {len(out_rows)} rows matching database.py!")
