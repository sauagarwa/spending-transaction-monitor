#!/usr/bin/env python3
import csv
import uuid
from decimal import Decimal, InvalidOperation
from datetime import datetime
import psycopg2
import psycopg2.extras as extras
import argparse

# ---------- Helpers ----------
def to_dt(s, fmt):
    if not s:
        return None
    try:
        return datetime.strptime(s, fmt)
    except Exception:
        return None

def to_decimal(s):
    if s is None or s == "":
        return None
    try:
        return Decimal(s)
    except InvalidOperation:
        return None

def to_float(s):
    if s is None or s == "":
        return None
    try:
        return float(s)
    except ValueError:
        return None

def gen_email(first, last):
    if not first or not last:
        return None
    return f"{first.strip().lower()}.{last.strip().lower()}@example.com"

# ---------- Main ----------
def main():
    ap = argparse.ArgumentParser(description="Load CSV into Postgres User and Transaction tables.")
    ap.add_argument("--dsn", required=True, help="Postgres DSN, e.g. 'host=localhost dbname=frauddb user=me password=secret'")
    ap.add_argument("--csv", required=True, help="Path to input CSV")
    ap.add_argument("--batch", type=int, default=1000, help="Batch size for inserts")
    args = ap.parse_args()

    # connection_string = "host=localhost dbname=spending_monitor user=postgres password=password"
    conn = psycopg2.connect(args.dsn)
    conn.autocommit = False
    cur = conn.cursor()

    print("⚠️  Deleting existing rows from User and Transaction...")
    cur.execute('TRUNCATE TABLE "transactions" RESTART IDENTITY CASCADE;')
    cur.execute('TRUNCATE TABLE "users" RESTART IDENTITY CASCADE;')
    conn.commit()

 

    # ---------- Upsert statements ----------
    # Note: we treat email as the unique key to dedupe users created from the same first/last
    upsert_user_sql = """
    INSERT INTO "users" (
        id, email, "first_name", "last_name",
        "address_street", "address_city", "address_state", "address_zipcode",
        "address_country",
        "last_merchant_latitude", "last_merchant_longitude", "last_transaction_timestamp",
        "last_merchant_city", "last_merchant_state", "last_merchant_country",
        "created_at", "updated_at"
    )
    VALUES (
        %(id)s, %(email)s, %(first_name)s, %(last_name)s,
        %(address_street)s, %(address_city)s, %(address_state)s, %(address_zipcode)s,
        %(address_country)s,
        %(last_merchant_latitude)s, %(last_merchant_longitude)s, %(last_transaction_timestamp)s,
        %(last_merchant_city)s, %(last_merchant_state)s, %(last_merchant_country)s,
        %(created_at)s, %(updated_at)s
    )
    ON CONFLICT (email) DO UPDATE SET
        "updated_at" = CURRENT_TIMESTAMP,
        "last_merchant_latitude"  = EXCLUDED."last_merchant_latitude",
        "last_merchant_longitude" = EXCLUDED."last_merchant_longitude",
        "last_transaction_timestamp" = EXCLUDED."last_transaction_timestamp",
        "last_merchant_city"      = EXCLUDED."last_merchant_city",
        "last_merchant_state"     = EXCLUDED."last_merchant_state",
        "last_merchant_country"   = EXCLUDED."last_merchant_country"
    RETURNING id;
    """

    insert_txn_sql = """
    INSERT INTO "transactions" (
        id, trans_num, "user_id", "credit_card_num",
        "first_name", "last_name", amount, currency, description,
        "merchant_name", "merchant_category", "transaction_date", "transaction_type",
        "merchant_latitude", "merchant_longitude", "merchant_city", "merchant_state", "merchant_country",
        status, "authorization_code", "reference_number", "created_at", "updated_at"

    ) VALUES (
        %(id)s, %(trans_num)s, %(user_id)s, %(credit_card_num)s,
        %(first_name)s, %(last_name)s, %(amount)s, %(currency)s, %(description)s,
        %(merchant_name)s, %(merchant_category)s, %(transaction_date)s, %(transaction_type)s,
        %(merchant_latitude)s, %(merchant_longitude)s, %(merchant_city)s, %(merchant_state)s, %(merchant_country)s,
        %(status)s, %(authorization_code)s, %(reference_number)s, %(created_at)s, %(updated_at)s
    );
    """

    # ---------- Read & load ----------
    user_cache = {}  # email -> UUID to avoid RETURNING roundtrip per duplicate within batch

    batch_users = []
    batch_txns  = []

    def flush_batches():
        if not batch_users and not batch_txns:
            return
        try:
            # Upsert users one-by-one to capture RETURNING id correctly
            for u in batch_users:
                cur.execute(upsert_user_sql, u)
                uid = cur.fetchone()[0]
                user_cache[u["email"]] = uid

            if batch_txns:
                extras.execute_batch(cur, insert_txn_sql, batch_txns, page_size=1000)

            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            batch_users.clear()
            batch_txns.clear()
    with open(args.csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader, start=1):
            # Parse primitives
            first = (row.get("first") or "").strip()
            last  = (row.get("last") or "").strip()

            email = gen_email(first, last)
            trans_dt = to_dt(row.get("trans_date_trans_time", ""), "%Y-%m-%d %H:%M:%S")
            amt      = to_decimal(row.get("amt"))
            merch_lat  = to_float(row.get("merch_lat"))
            merch_long = to_float(row.get("merch_long"))

            # Build / upsert User
            # Using merchant coords as "last transaction" snapshot; address from customer fields
            user_id = user_cache.get(email)
            if not user_id:
                u = {
                    "id": str(uuid.uuid4()),
                    "email": email,
                    "first_name": first or "Unknown",
                    "last_name":  last or "Unknown",
                    "address_street": row.get("street") or None,
                    "address_city":   row.get("city") or None,
                    "address_state":  row.get("state") or None,
                    "address_zipcode": (row.get("zip") or "").strip() or None,
                    "address_country": "US",
                    "last_merchant_latitude":  merch_lat,
                    "last_merchant_longitude": merch_long,
                    "last_transaction_timestamp": trans_dt,
                    "last_merchant_city":      row.get("city") or None,
                    "last_merchant_state":     row.get("state") or None,
                    "last_merchant_country":   "US",
                    "created_at": datetime.now(),
                    "updated_at": datetime.now(),
                }
                batch_users.append(u)
                user_cache[u["email"]] = u["id"]
            # Prepare Transaction
            txn = {
                "id": str(uuid.uuid4()),
                "trans_num": (row.get("trans_num") or "").strip(),
                "user_id": user_cache.get(email) or u["id"],  # u is defined if user not cached
                "credit_card_num": (row.get("cc_num") or "").strip() or None,

                "first_name": first or "Unknown",
                "last_name":  last or "Unknown",
                "amount": amt if amt is not None else Decimal("0.00"),
                "currency": "USD",
                "description": f"Purchase at {row.get('merchant')}" if row.get("merchant") else None,

                "merchant_name": (row.get("merchant") or "").strip() or None,
                "merchant_category": (row.get("category") or "").strip() or None,
                "transaction_date": trans_dt,
                "transaction_type": "PURCHASE",

                "merchant_latitude":  merch_lat,
                "merchant_longitude": merch_long,
                "merchant_city":      row.get("city") or None,
                "merchant_state":     row.get("state") or None,
                "merchant_country":   "US",
                "merchant_zipcode":   (row.get("zip") or "").strip() or None,

                "status": "APPROVED",           # is_fraud intentionally UNUSED
                "authorization_code": None,
                "reference_number":   (row.get("row_id") or "").strip() or None,
                "created_at": datetime.now(),
                "updated_at": datetime.now(),
            }

            batch_txns.append(txn)

            if (i % args.batch) == 0:
                flush_batches()

    # Flush final batch
    flush_batches()

    cur.close()
    conn.close()
    print("✅ Load complete: User & Transaction populated (is_fraud ignored).")

if __name__ == "__main__":
    main()