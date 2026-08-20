"""Sanity checks over the generated files. Run after generate.py."""
import csv, os, collections, datetime

D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")

def load(name):
    with open(os.path.join(D, name), newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))

acc = load("accounts.csv"); pay = load("payments.csv")
arr = load("payment_arrangements.csv"); cli = load("clients.csv"); usr = load("users.csv")
notes = load("notes.csv")

print(f"rows: accounts={len(acc)} payments={len(pay)} arrangements={len(arr)} notes={len(notes)}")

# 1. System fields must never be blank
for col in ("account_id","client_account_number","placement_date","account_status","status_date",
            "original_balance","placement_balance","current_balance","product_type","client_id"):
    blanks = sum(1 for a in acc if not a[col].strip())
    print(f"  blank {col:26} {blanks}")

# 2. Status mix
c = collections.Counter(a["account_status"] for a in acc)
CLOSED = {"PAID_IN_FULL","SETTLED_IN_FULL","RETURNED","RECALLED","BANKRUPTCY","DECEASED","UNCOLLECTIBLE","STATUTE_EXPIRED"}
print("status mix:", ", ".join(f"{k}={v}" for k,v in c.most_common()))
print("closed pct:", round(sum(v for k,v in c.items() if k in CLOSED)/len(acc)*100,1))

# 3. Specialized fields confined to their status
bk_pop = [a for a in acc if a["bankruptcy_case_number"].strip()]
bk_status = [a for a in acc if a["account_status"]=="BANKRUPTCY"]
print(f"bankruptcy status={len(bk_status)}  case# populated={len(bk_pop)}  "
      f"case# on non-BK={sum(1 for a in bk_pop if a['account_status']!='BANKRUPTCY')}  "
      f"BK missing case#={sum(1 for a in bk_status if not a['bankruptcy_case_number'].strip())}  "
      f"BK missing chapter={sum(1 for a in bk_status if not a['bankruptcy_chapter'].strip())}")
dec = [a for a in acc if a["account_status"]=="DECEASED"]
dpop = [a for a in acc if a["deceased_date"].strip()]
print(f"deceased status={len(dec)}  date populated={len(dpop)}  "
      f"date on non-deceased={sum(1 for a in dpop if a['account_status']!='DECEASED')}  "
      f"missing date={sum(1 for a in dec if not a['deceased_date'].strip())}")

# 4. Address completeness
incomplete = sum(1 for a in acc if not (a["address_line1"].strip() and a["city"].strip()
                 and a["state"].strip() and a["zip_code"].strip()))
print(f"accounts with incomplete address: {incomplete} ({incomplete/len(acc)*100:.1f}%)")
print(f"zip not 5 digits: {sum(1 for a in acc if a['zip_code'] and len(a['zip_code'])!=5)}")

# 5. Placement dates span
pd = sorted(a["placement_date"] for a in acc)
print(f"placement_date range: {pd[0]} .. {pd[-1]}")
print(f"placements by year: {dict(sorted(collections.Counter(p[:4] for p in pd).items()))}")

# 6. Referential integrity
acc_ids = {a["account_id"] for a in acc}; usr_ids = {u["user_id"] for u in usr}
cli_ids = {c["client_id"] for c in cli}
print(f"orphan payments={sum(1 for p in pay if p['account_id'] not in acc_ids)}"
      f"  orphan arrangements={sum(1 for r in arr if r['account_id'] not in acc_ids)}"
      f"  orphan notes={sum(1 for n in notes if n['account_id'] not in acc_ids)}"
      f"  bad client_id={sum(1 for a in acc if a['client_id'] not in cli_ids)}"
      f"  bad assigned_user={sum(1 for a in acc if a['assigned_user_id'] not in usr_ids)}"
      f"  bad note user={len({n['note_id'] for n in notes if n['user_id'] not in usr_ids})}")

# 7. Notes distribution & ordering
per = collections.Counter(n["account_id"] for n in notes)
print(f"notes/account: min={min(per.values())} max={max(per.values())} avg={sum(per.values())/len(per):.1f} "
      f"accounts with no notes={len(acc_ids)-len(per)}")
early = sum(1 for n in notes if n["account_id"] in acc_ids and
            n["note_datetime"][:10] < next(a["placement_date"] for a in acc if a["account_id"]==n["account_id"])) if False else "skipped"
oh = sum(1 for n in notes if n["contact_type"]=="OUTBOUND_CALL" and not (8 <= int(n["note_datetime"][11:13]) < 21))
print(f"outbound calls outside 8a-9p: {oh}")
print(f"multiline note_text rows: {sum(1 for n in notes if chr(10) in n['note_text'])}")
print(f"physical lines in notes.csv: {sum(1 for _ in open(os.path.join(D,'notes.csv'), encoding='utf-8')):,}")

# 8. Money reconciliation
posted = collections.defaultdict(float)
for p in pay:
    if p["payment_status"]=="POSTED":
        try: posted[p["account_id"]] += float(p["payment_amount"])
        except ValueError: pass
mismatch = 0
for a in acc:
    try: tp = float(a["total_paid"].replace("$","").replace(",",""))
    except ValueError: continue
    if abs(tp - posted.get(a["account_id"],0.0)) > 0.05: mismatch += 1
print(f"accounts where total_paid != sum(POSTED payments): {mismatch}")
print(f"accounts with last_payment_date but no payment rows: "
      f"{sum(1 for a in acc if a['last_payment_date'] and a['account_id'] not in {p['account_id'] for p in pay})}")

# 9. Numeric parse failures (planted)
bad_num = sum(1 for a in acc if a["current_balance"] and not a["current_balance"].replace("-","").replace(".","").isdigit())
print(f"current_balance cells that will not parse as a number: {bad_num}")
print(f"negative current_balance: {sum(1 for a in acc if a['current_balance'].startswith('-'))}")

# 10. Duplicates
key = collections.Counter((a["client_id"], a["client_account_number"]) for a in acc)
print(f"duplicate client_id+client_account_number groups: {sum(1 for v in key.values() if v>1)}")
ssn = collections.Counter(a["ssn"] for a in acc if a["ssn"].strip())
print(f"SSNs used by >1 account: {sum(1 for v in ssn.values() if v>1)}  max reuse={max(ssn.values())}")
