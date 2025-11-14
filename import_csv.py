# import_csv.py
import csv
import os
from sqlalchemy.exc import IntegrityError
from app import create_app
from models import db, Bank, Branch
from sqlalchemy import select

DB_PATH = os.environ.get("DATABASE_URL", "sqlite:///data.db")
CSV_PATH = os.environ.get("CSV_PATH", "bank_branches.csv")
CHUNK_SIZE = 2000  # tune for memory and speed

app = create_app()
app.app_context().push()

def get_or_create_bank(session, bank_name, bank_cache):
    if not bank_name:
        bank_name = "UNKNOWN"
    # simple cache for bank name -> id
    if bank_name in bank_cache:
        return bank_cache[bank_name]
    b = session.query(Bank).filter_by(name=bank_name).first()
    if b:
        bank_cache[bank_name] = b.id
        return b.id
    new_b = Bank(name=bank_name)
    session.add(new_b)
    session.flush()  # get id
    bank_cache[bank_name] = new_b.id
    return new_b.id

def normalize_header(h):
    return h.strip().lower()

def import_csv(csv_path=CSV_PATH):
    session = db.session
    bank_cache = {}
    rows_to_insert = []

    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        # map common CSV headers to model fields
        header_map = {}
        for h in reader.fieldnames:
            key = normalize_header(h)
            if 'bank' in key and 'name' in key:
                header_map['bank_name'] = h
            elif key in ('bank', 'bankname', 'bank_name'):
                header_map['bank_name'] = h
            elif 'ifsc' in key:
                header_map['ifsc'] = h
            elif 'branch' == key or 'branchname' in key or 'branch_name' in key:
                header_map['branch'] = h
            elif 'address' in key:
                header_map['address'] = h
            elif 'city' in key:
                header_map['city'] = h
            elif 'district' in key:
                header_map['district'] = h
            elif 'state' in key:
                header_map['state'] = h
            elif 'micr' in key:
                header_map['micr'] = h
        # fallback for missing important header:
        if 'ifsc' not in header_map:
            raise RuntimeError("CSV missing IFSC column (can't proceed). Found headers: " + ", ".join(reader.fieldnames))

        count = 0
        for row in reader:
            bank_name = row.get(header_map.get('bank_name', ''), '').strip()
            ifsc = row.get(header_map['ifsc'], '').strip()
            if not ifsc:
                continue  # ignore invalid rows
            branch_name = row.get(header_map.get('branch',''), '').strip()
            address = row.get(header_map.get('address',''), '').strip()
            city = row.get(header_map.get('city',''), '').strip()
            district = row.get(header_map.get('district',''), '').strip()
            state = row.get(header_map.get('state',''), '').strip()
            micr = row.get(header_map.get('micr',''), '').strip()

            # get/create bank id (cached)
            bank_id = get_or_create_bank(session, bank_name, bank_cache)

            rows_to_insert.append({
                "ifsc": ifsc,
                "bank_id": bank_id,
                "branch": branch_name,
                "address": address,
                "city": city,
                "district": district,
                "state": state,
                "micr": micr
            })
            count += 1

            if len(rows_to_insert) >= CHUNK_SIZE:
                session.bulk_insert_mappings(Branch, rows_to_insert)
                session.commit()
                print(f"Inserted {count} rows...")
                rows_to_insert = []

        if rows_to_insert:
            session.bulk_insert_mappings(Branch, rows_to_insert)
            session.commit()
            print(f"Inserted final chunk. Total rows: {count}")

if __name__ == "__main__":
    print("Creating DB tables (if not exist)...")
    db.create_all()
    import_csv()
    print("Done.")
