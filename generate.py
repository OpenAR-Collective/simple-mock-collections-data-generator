"""
Mock data generator for "Acme Receivables Management", a fictional third-party
debt collection agency.

Produces a small flat-file "database" that behaves like real collections data:

    data/clients.csv               placing creditors
    data/users.csv                 agency staff
    data/accounts.csv              accounts, with consumer data flattened in
    data/payments.csv              payment history
    data/payment_arrangements.csv  promises and installment plans
    data/notes.csv                 collection activity notes (largest table)

Everything is deterministic: the same seed produces byte-identical files.
All names, addresses, SSNs, phone numbers and account numbers are synthetic.

Deliberate data quality defects are planted throughout and recorded in
ANSWER_KEY.md as they are applied, so the catalog can never drift from the
data it describes.

Usage
-----
    python generate.py [--seed SEED] [--out DIR] [--key PATH] [--accounts N]

    --seed SEED     Any text or integer. Default: "Sample Seed". The same seed
                    and the same version of this script always produce the same
                    files, so a seed is how you name a data set rather than how
                    you randomize it. A digits-only value is read as an integer,
                    so --seed 12345 and --seed "12345" are the same data set.

    --out DIR       Directory to write the six CSV files into, created if it does
                    not exist, relative to this script unless absolute.
                    Default: data

    --key PATH      Where to write the answer key, relative to this script unless
                    absolute. Default: ANSWER_KEY.md

    --accounts N    Number of accounts to generate. Every other file scales with
                    it, so N=500 gives a set small enough to open in a
                    spreadsheet. Default: 10000

Examples
--------
    python generate.py
    python generate.py --accounts 500 --out sample
    python generate.py --seed "Data Set A" --out data_a --key ANSWER_KEY_A.md
    python generate.py --seed "Data Set B" --out data_b --key ANSWER_KEY_B.md

The last two are the matched pair ab_check.py expects: same model, different
noise, so a scorecard fitted on A can be tested honestly on B.
"""

import argparse
import csv
import math
import os
import random
from datetime import date, datetime, timedelta

from refdata import (AREA_CODES, BK_DISTRICTS, CITIES, EMAIL_DOMAINS, EMPLOYERS,
                     FIRST_NAMES_F, FIRST_NAMES_M, LAST_NAMES, MIDDLE_INITIALS,
                     STREET_NAMES, STREET_TYPES, SUFFIXES, UNIT_TYPES)

# A text seed is stable across machines: Python derives it from a SHA-512 of the
# text rather than from hash(), so PYTHONHASHSEED has no effect on it.
SEED = "Sample Seed"          # any text will work, as will any integer
ACCOUNT_COUNT = 10_000
TODAY = date(2026, 8, 20)                         # "now" for the whole data set
# Mean and spread of collector-driven activity notes per account. System notes
# (placement, letters, payments, status changes) are added on top, which brings
# the finished file to roughly 20 notes per account.
NOTE_ACTIVITY_MEAN = 16
NOTE_ACTIVITY_SD = 6
HISTORY_START = TODAY - timedelta(days=1826)      # placements span 5 years
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(BASE_DIR, "data")        # overridden by --out
KEY_PATH = os.path.join(BASE_DIR, "ANSWER_KEY.md")   # overridden by --key

rnd = random.Random(SEED)

# Registry of planted defects, written out as the answer key.
ISSUES = []


def record(code, table, columns, description, ids, hint=""):
    """Log a planted data quality defect for the answer key."""
    ids = list(ids)
    ISSUES.append({
        "code": code, "table": table, "columns": columns,
        "description": description, "count": len(ids),
        "samples": ids[:6], "hint": hint,
    })
    return ids


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------

def iso(d):
    return d.isoformat() if d else ""


def ts(dt):
    return dt.strftime("%Y-%m-%d %H:%M:%S") if dt else ""


def money(x):
    return f"{x:.2f}"


def pick(seq):
    return rnd.choice(seq)


def chance(p):
    return rnd.random() < p


def weighted(options):
    """options: list of (value, weight)."""
    total = sum(w for _, w in options)
    r = rnd.random() * total
    upto = 0.0
    for value, w in options:
        upto += w
        if r <= upto:
            return value
    return options[-1][0]


def rand_date(start, end):
    span = (end - start).days
    if span <= 0:
        return start
    return start + timedelta(days=rnd.randint(0, span))


def skewed_amount(low, high, skew=1.7):
    """Log-scaled draw biased toward the low end, the way real balances sit."""
    u = rnd.random() ** skew
    return round(low * ((high / low) ** u), 2)


def business_dt(d, early=8, late=20):
    """A plausible timestamp on day d, inside normal calling hours."""
    hour = rnd.randint(early, late - 1)
    return datetime(d.year, d.month, d.day, hour, rnd.randint(0, 59), rnd.randint(0, 59))


# --------------------------------------------------------------------------
# Clients
# --------------------------------------------------------------------------

# Creditors that place accounts with the agency.
#
# "lift" is the client's own contribution to liquidation in log-odds, on top of
# what the debt is for. It stands in for the things that genuinely vary between
# creditors: how clean the data they send is, how hard they worked the account
# before placing it, and who their customers are. Clients inside the same product
# class deliberately differ, so client and product type are separate signals.
#
# A few clients place more than one kind of paper, which is what makes client and
# product type separable at all rather than perfectly collinear.
CLIENT_SPECS = [
    {"name": "Mercy Regional Health System", "industry": "Healthcare", "prefix": "MRH",
     "digits": 9, "rate": 22.5, "weight": 12, "lift": 0.18,
     "products": [("MEDICAL", 1.0)]},
    {"name": "Northside Family Practice PLLC", "industry": "Healthcare", "prefix": "NFP",
     "digits": 7, "rate": 28.0, "weight": 5, "lift": -0.12, "no_settlement": True,
     "products": [("MEDICAL", 1.0)]},
    {"name": "Cascade Valley Medical Center", "industry": "Healthcare", "prefix": "CVM",
     "digits": 10, "rate": 24.0, "weight": 6, "lift": 0.02,
     "products": [("MEDICAL", 1.0)]},
    {"name": "Pinnacle Dental Group", "industry": "Healthcare", "prefix": "PDG",
     "digits": 7, "rate": 30.0, "weight": 4, "lift": 0.10,
     "products": [("DENTAL", 1.0)]},
    {"name": "Brightline Dental Partners", "industry": "Healthcare", "prefix": "BDP",
     "digits": 8, "rate": 31.0, "weight": 3, "lift": -0.14, "no_email": True,
     "products": [("DENTAL", 1.0)]},
    {"name": "Summit Peak Bank, N.A.", "industry": "Banking", "prefix": "",
     "digits": 12, "rate": 30.0, "weight": 12, "lift": 0.12, "interest": True,
     "products": [("CREDIT_CARD", 0.75), ("PERSONAL_LOAN", 0.25)]},
    {"name": "Granite State Bankcard", "industry": "Banking", "prefix": "GSB",
     "digits": 11, "rate": 29.5, "weight": 7, "lift": -0.16, "interest": True,
     "products": [("CREDIT_CARD", 1.0)]},
    {"name": "Sunbelt Retail Card Services", "industry": "Retail Credit", "prefix": "SB",
     "digits": 12, "rate": 31.0, "weight": 7, "lift": 0.06, "interest": True,
     "products": [("RETAIL_CARD", 0.8), ("CREDIT_CARD", 0.2)]},
    {"name": "Cardinal Financial Services", "industry": "Consumer Lending", "prefix": "CFS-",
     "digits": 8, "rate": 32.5, "weight": 8, "lift": -0.08, "interest": True,
     "products": [("PERSONAL_LOAN", 0.7), ("RETAIL_CARD", 0.3)]},
    {"name": "Riverbend Credit Union", "industry": "Banking", "prefix": "RB",
     "digits": 10, "rate": 27.0, "weight": 5, "lift": 0.22, "interest": True,
     "products": [("AUTO_DEFICIENCY", 1.0)]},
    {"name": "Silverline Auto Finance", "industry": "Auto Finance", "prefix": "SL",
     "digits": 10, "rate": 29.0, "weight": 5, "lift": -0.20, "interest": True,
     "products": [("AUTO_DEFICIENCY", 1.0)]},
    {"name": "Metro Utilities Authority", "industry": "Utilities", "prefix": "",
     "digits": 11, "rate": 18.0, "weight": 9, "lift": 0.14, "fee": True,
     "products": [("UTILITY", 1.0)]},
    {"name": "Ridgeline Power & Water", "industry": "Utilities", "prefix": "RPW",
     "digits": 9, "rate": 19.5, "weight": 5, "lift": -0.10, "fee": True,
     "products": [("UTILITY", 1.0)]},
    {"name": "Clearwave Communications", "industry": "Telecom", "prefix": "CW",
     "digits": 12, "rate": 24.0, "weight": 8, "lift": -0.06, "fee": True, "dob_us_format": True,
     "products": [("TELECOM", 1.0)]},
    {"name": "Northstar Wireless", "industry": "Telecom", "prefix": "NSW",
     "digits": 10, "rate": 25.5, "weight": 5, "lift": 0.16, "fee": True,
     "products": [("TELECOM", 1.0)]},
    {"name": "Apex Property Management", "industry": "Property Management", "prefix": "APM",
     "digits": 6, "rate": 35.0, "weight": 4, "lift": -0.18, "fee": True,
     "products": [("RENTAL", 1.0)]},
    {"name": "Cornerstone Residential Group", "industry": "Property Management", "prefix": "CRG",
     "digits": 8, "rate": 34.0, "weight": 3, "lift": 0.08, "fee": True,
     "products": [("RENTAL", 1.0)]},
    {"name": "Greenfield Student Aid Servicing", "industry": "Education Finance", "prefix": "GSA",
     "digits": 11, "rate": 26.0, "weight": 3, "lift": 0.00, "interest": True,
     "products": [("STUDENT_LOAN", 1.0)]},
    {"name": "Titan Fitness Clubs", "industry": "Fitness", "prefix": "TFC",
     "digits": 6, "rate": 40.0, "weight": 6, "lift": -0.05, "fee": True,
     "lapsed": True, "inactive": True, "products": [("GYM_MEMBERSHIP", 1.0)]},
    {"name": "Harbor Point Veterinary", "industry": "Veterinary", "prefix": "HPV",
     "digits": 6, "rate": 33.0, "weight": 3, "lift": 0.05,
     "products": [("VETERINARY", 1.0)]},
    {"name": "Lakeshore Insurance Recovery", "industry": "Insurance", "prefix": "LIR",
     "digits": 9, "rate": 25.0, "weight": 3, "lift": 0.00, "no_settlement": True,
     "products": [("SUBROGATION", 1.0)]},
    # A second client code for Mercy Regional. Agencies carry these routinely, for
    # separate facilities, contract revisions or billing systems, and they share the
    # same underlying client, so this record carries the same lift as the first one.
    {"name": "Mercy Regional Health Sys.", "industry": "Healthcare", "prefix": "MRH",
     "digits": 9, "rate": 22.5, "weight": 3, "lift": 0.18, "inactive": True,
     "products": [("MEDICAL", 1.0)]},
]

PHONE_FORMATS = ["###-###-####", "(###) ###-####", "##########", "###.###.####"]


def build_clients():
    clients = []
    lapsed_id = dup_ids = no_email_id = None
    for i, spec in enumerate(CLIENT_SPECS, start=1):
        client_id = 100 + i
        name, prefix = spec["name"], spec["prefix"]
        interest, fee = spec.get("interest", False), spec.get("fee", False)
        city, state, zip5 = pick(CITIES)
        # Every contract predates the placement window, so the only contract-window
        # problem in the data is the deliberate one below.
        start = rand_date(date(2015, 1, 1), HISTORY_START - timedelta(days=30))
        # One client's contract has lapsed but placements keep arriving (defect C2).
        if spec.get("lapsed"):
            end = date(2025, 3, 31)
            lapsed_id = client_id
        else:
            end = TODAY + timedelta(days=rnd.randint(200, 1800))
        if spec.get("no_email"):
            no_email_id = client_id
        contact_first = pick(FIRST_NAMES_F + FIRST_NAMES_M)
        contact_last = pick(LAST_NAMES)
        # The product listed on the client record is the one they place most of.
        primary = max(spec["products"], key=lambda p: p[1])[0]
        clients.append({
            "client_id": client_id,
            "client_code": (prefix.strip("-") or name[:3].upper())[:4].upper() + str(i).zfill(2),
            "client_name": name,
            "industry": spec["industry"],
            "primary_product_type": primary,
            "contact_name": f"{contact_first} {contact_last}",
            "contact_email": ("" if spec.get("no_email") else
                              f"{contact_first[0].lower()}{contact_last.lower()}"
                              f"@{name.split()[0].lower().strip(',')}.com"),
            "contact_phone": f"{pick(AREA_CODES[state])}-555-{make_line_number():04d}",
            "address_line1": f"{rnd.randint(100, 8999)} {pick(STREET_NAMES)} {pick(STREET_TYPES)}",
            "city": city, "state": state, "zip_code": zip5,
            "contract_start_date": iso(start),
            "contract_end_date": iso(end),
            "contingency_rate_pct": f"{spec['rate']:.1f}",
            "allows_interest": "Y" if interest else "N",
            "interest_rate_pct": f"{rnd.choice([6.0, 8.0, 9.5, 12.0]):.1f}" if interest else "0.0",
            "allows_fees": "Y" if fee else "N",
            "allows_settlement": "N" if spec.get("no_settlement") else "Y",
            "min_settlement_pct": str(rnd.choice([50, 55, 60, 65, 70])),
            "client_status": "INACTIVE" if spec.get("inactive") else "ACTIVE",
            "_prefix": prefix, "_digits": spec["digits"], "_products": spec["products"],
            "_interest": interest, "_fee": fee, "_weight": spec["weight"],
            "_lift": spec["lift"],
            "_phone_format": PHONE_FORMATS[i % len(PHONE_FORMATS)],
            "_ssn_dashes": i % 3 != 0,
            "_dob_us_format": bool(spec.get("dob_us_format")),
        })
    dup_ids = [c["client_id"] for c in clients if c["client_name"].startswith("Mercy Regional")]
    record("C1", "clients", "client_name",
           "Two client codes for the same creditor, Mercy Regional Health System. Agencies carry "
           "these routinely, for separate facilities, contract revisions or billing systems, so it "
           "is not an error. It still splits any report that groups by client_id, and the two "
           "records liquidate identically because they are the same client.",
           dup_ids, "Compare account counts, balances and liquidation by client_name against client_id.")
    record("C2", "clients", "contract_end_date",
           "Client contract ended 2025-03-31 but accounts were placed under it afterward.",
           [lapsed_id], "Join accounts.placement_date against clients.contract_end_date.")
    record("C3", "clients", "contact_email", "Client record missing a contact email.", [no_email_id])
    return clients


CLIENT_COLUMNS = ["client_id", "client_code", "client_name", "industry", "primary_product_type",
                  "contact_name", "contact_email", "contact_phone", "address_line1", "city",
                  "state", "zip_code", "contract_start_date", "contract_end_date",
                  "contingency_rate_pct", "allows_interest", "interest_rate_pct", "allows_fees",
                  "allows_settlement", "min_settlement_pct", "client_status"]


# --------------------------------------------------------------------------
# Users
# --------------------------------------------------------------------------

USER_COLUMNS = ["user_id", "username", "first_name", "last_name", "email", "role", "team",
                "manager_user_id", "phone_extension", "hire_date", "termination_date",
                "user_status", "monthly_goal_amount", "last_login_date"]

ROLE_PLAN = ([("SYSTEM", 1), ("ADMIN", 2), ("MANAGER", 2), ("SUPERVISOR", 4), ("TEAM_LEAD", 4),
              ("SR_COLLECTOR", 6), ("COLLECTOR", 26), ("COMPLIANCE", 2), ("LEGAL_SPECIALIST", 2)])
TEAMS = ["ALPHA", "BRAVO", "CHARLIE", "EARLY_OUT", "LEGAL"]


def build_users():
    users = []
    uid = 1000
    for role, count in ROLE_PLAN:
        for _ in range(count):
            uid += 1
            if role == "SYSTEM":
                users.append({
                    "user_id": uid, "username": "system", "first_name": "System",
                    "last_name": "Process", "email": "noreply@acmereceivables.com",
                    "role": "SYSTEM", "team": "", "manager_user_id": "", "phone_extension": "",
                    "hire_date": "2015-01-01", "termination_date": "", "user_status": "ACTIVE",
                    "monthly_goal_amount": "", "last_login_date": "",
                })
                continue
            first = pick(FIRST_NAMES_F + FIRST_NAMES_M)
            last = pick(LAST_NAMES)
            hire = rand_date(date(2014, 1, 1), date(2026, 5, 1))
            # About a fifth of staff have left; collections has high turnover.
            terminated = chance(0.22) and hire < date(2025, 6, 1)
            term_date = rand_date(hire + timedelta(days=120), TODAY) if terminated else None
            status = "TERMINATED" if terminated else weighted([("ACTIVE", 0.93), ("LOA", 0.04), ("INACTIVE", 0.03)])
            team = "LEGAL" if role == "LEGAL_SPECIALIST" else ("" if role in ("ADMIN", "COMPLIANCE", "MANAGER") else pick(TEAMS[:4]))
            goal = {"COLLECTOR": 45000, "SR_COLLECTOR": 65000, "TEAM_LEAD": 80000}.get(role, "")
            users.append({
                "user_id": uid,
                "username": f"{first[0].lower()}{last.lower()}"[:14],
                "first_name": first, "last_name": last,
                "email": f"{first[0].lower()}{last.lower()}@acmereceivables.com",
                "role": role, "team": team, "manager_user_id": "",
                "phone_extension": str(2000 + (uid - 1000)),
                "hire_date": iso(hire), "termination_date": iso(term_date),
                "user_status": status,
                "monthly_goal_amount": money(goal) if goal else "",
                "last_login_date": iso(term_date if terminated else rand_date(TODAY - timedelta(days=45), TODAY)),
            })
    supervisors = [u["user_id"] for u in users if u["role"] in ("SUPERVISOR", "TEAM_LEAD")]
    managers = [u["user_id"] for u in users if u["role"] == "MANAGER"]
    for u in users:
        if u["role"] in ("COLLECTOR", "SR_COLLECTOR"):
            u["manager_user_id"] = str(pick(supervisors))
        elif u["role"] in ("SUPERVISOR", "TEAM_LEAD", "COMPLIANCE", "LEGAL_SPECIALIST"):
            u["manager_user_id"] = str(pick(managers))

    # Defect U2: duplicate username across two active staff.
    dupe_pair = [u for u in users if u["role"] == "COLLECTOR"][:2]
    dupe_pair[1]["username"] = dupe_pair[0]["username"]
    record("U1", "users", "username", "Two different user_ids share one username.",
           [u["user_id"] for u in dupe_pair])
    # Defect U4: missing email addresses.
    missing_email = [u for u in users if u["role"] == "COLLECTOR"][3:5]
    for u in missing_email:
        u["email"] = ""
    record("U2", "users", "email", "Active users with no email address on file.",
           [u["user_id"] for u in missing_email])
    return users


# --------------------------------------------------------------------------
# Account status model
# --------------------------------------------------------------------------

PLAN_STATUSES = {"PAYMENT_PLAN", "PAYMENT_PLAN_AT_RISK"}

# status_class is a denormalized rollup of account_status, one class per account.
# CLOSED    the account is finished, whatever the reason
# PTP       the consumer has a live commitment to pay, either a promise or a plan
# SENSITIVE still open, but standard collection activity has to stop until it is resolved
# OPEN      normal collectible inventory
STATUS_CLASS = {
    "NEW": "OPEN", "ACTIVE": "OPEN", "SKIP_TRACE": "OPEN", "SKIP_NO_HIT": "OPEN",
    "CLIENT_HOLD": "OPEN", "PENDING_CLIENT_REVIEW": "OPEN",
    "PROMISE_TO_PAY": "PTP", "PAYMENT_PLAN": "PTP", "PAYMENT_PLAN_AT_RISK": "PTP",
    "DISPUTED": "SENSITIVE", "LEGAL": "SENSITIVE", "MILITARY_SCRA": "SENSITIVE",
    "HARDSHIP_REVIEW": "SENSITIVE",
    "PAID_IN_FULL": "CLOSED", "SETTLED_IN_FULL": "CLOSED", "RETURNED": "CLOSED",
    "RECALLED": "CLOSED", "BANKRUPTCY": "CLOSED", "DECEASED": "CLOSED",
    "UNCOLLECTIBLE": "CLOSED", "STATUTE_EXPIRED": "CLOSED",
}

CLOSED_SET = {s for s, cls in STATUS_CLASS.items() if cls == "CLOSED"}

CLOSE_REASONS = {
    "PAID_IN_FULL": "PAID IN FULL", "SETTLED_IN_FULL": "SETTLEMENT SATISFIED",
    "RETURNED": "RETURNED TO CLIENT - UNCOLLECTIBLE", "RECALLED": "RECALLED BY CLIENT",
    "BANKRUPTCY": "BANKRUPTCY - COLLECTION CEASED", "DECEASED": "CONSUMER DECEASED",
    "UNCOLLECTIBLE": "CLOSED UNCOLLECTIBLE", "STATUTE_EXPIRED": "OUT OF STATUTE",
}

BALANCE_RANGES = {
    "MEDICAL": (75, 14000), "DENTAL": (150, 6500), "CREDIT_CARD": (300, 22000),
    "RETAIL_CARD": (95, 4800), "PERSONAL_LOAN": (500, 18000), "AUTO_DEFICIENCY": (1500, 28000),
    "UTILITY": (60, 2600), "TELECOM": (45, 1900), "RENTAL": (400, 9500),
    "STUDENT_LOAN": (900, 45000), "GYM_MEMBERSHIP": (40, 950), "VETERINARY": (100, 5200),
    "SUBROGATION": (500, 30000),
}


def make_line_number():
    """
    A line number inside the 555 fiction exchange.

    555-0100 through 555-0199 is the block NANPA formally reserves for fictional
    use, so it gets the largest share. The rest of the 555 exchange is not
    assigned to subscriber lines either, which keeps enough range to avoid
    thousands of accidental shared numbers. 555-1212 is directory assistance and
    is the one value that is genuinely in service, so it is excluded.
    """
    if chance(0.35):
        return rnd.randint(100, 199)
    n = rnd.randint(0, 9999)
    return 100 if n == 1212 else n


def format_phone(state, fmt):
    digits = f"{pick(AREA_CODES[state])}555{make_line_number():04d}"
    if fmt == "##########":
        return digits
    if fmt == "(###) ###-####":
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    sep = "." if fmt == "###.###.####" else "-"
    return f"{digits[:3]}{sep}{digits[3:6]}{sep}{digits[6:]}"


# Group numbers the IRS uses for ITINs, which also begin with a 9. Avoiding them
# means a 9xx number here cannot collide with a real taxpayer identifier either.
ITIN_GROUPS = set(range(50, 66)) | set(range(70, 89)) | set(range(90, 93)) | set(range(94, 100))
SAFE_9XX_GROUPS = [g for g in range(1, 100) if g not in ITIN_GROUPS]


def make_ssn(dashes=True):
    """
    An SSN that looks real but cannot be one.

    The SSA has never issued a number with an area of 000, 666 or 900-999, with a
    group of 00, or with a serial of 0000, and none of those will ever be issued
    under the randomization scheme in use since 2011. Every number produced here
    breaks at least one of those rules, so none of them can belong to a person.

    The SSA also reserves 987-65-4320 through 987-65-4329 for advertising, but
    that block holds only ten values, so it is left to the placeholder junk in
    defect A11 rather than used here, where it would create thousands of
    accidental SSN collisions.
    """
    variant = weighted([("area_9xx", 0.50), ("area_666", 0.16), ("group_00", 0.24),
                        ("serial_0000", 0.10)])
    if variant == "area_9xx":
        a, g, s = rnd.randint(900, 999), pick(SAFE_9XX_GROUPS), rnd.randint(1, 9999)
    elif variant == "area_666":
        a, g, s = 666, rnd.randint(1, 99), rnd.randint(1, 9999)
    elif variant == "group_00":
        a, g, s = rnd.choice([rnd.randint(100, 665), rnd.randint(667, 899)]), 0, rnd.randint(1, 9999)
    else:
        a, g, s = rnd.choice([rnd.randint(100, 665), rnd.randint(667, 899)]), rnd.randint(1, 99), 0
    return f"{a:03d}-{g:02d}-{s:04d}" if dashes else f"{a:03d}{g:02d}{s:04d}"


def make_address(state):
    line1 = f"{rnd.randint(1, 19999)} {pick(STREET_NAMES)} {pick(STREET_TYPES)}"
    if chance(0.06):
        line1 = f"PO Box {rnd.randint(10, 9999)}"
    line2 = ""
    if chance(0.22):
        ut = pick(UNIT_TYPES)
        line2 = f"{ut} {rnd.randint(1, 40)}{pick('ABCDE') if chance(0.3) else ''}" if ut != "#" else f"#{rnd.randint(1, 250)}"
    return line1, line2


# --------------------------------------------------------------------------
# Propensity to pay
#
# Liquidation here is not random. Every account gets a latent propensity drawn
# from a logistic model over the things that actually drive collections
# performance, and that latent score then decides whether the account pays, how
# much and how often, what status it ends in, how its phone calls go, and what
# vendor score it carries.
#
# The coefficients are fixed constants, not seeded, so two data sets built with
# different seeds share one underlying model with different noise. A scorecard
# fitted on one should hold its shape on the other. The values are chosen to be
# plausible and to be learnable; they are not fitted to real portfolios, and
# nothing here should be read as an empirical claim about real consumers.
# --------------------------------------------------------------------------

PROPENSITY_INTERCEPT = -0.95
W_DEBT_AGE = -0.55            # per year between charge-off and placement
W_LOG_BALANCE = -0.52         # per 10x of placement balance above a $250 base
W_CLIENT_PAID = 0.75          # the consumer paid the original creditor at some point
W_CLIENT_PAID_RECENCY = 0.60  # and how recently, decaying to nothing over two years

# Contact data. The agency has done no skip tracing or address cleanup of its own,
# so these fields are exactly what the client sent, which makes them a real signal
# rather than an artifact of the agency's own record keeping. Collectively this is
# the strongest family in the model: you cannot collect from someone you cannot reach.
W_HAS_CELL = 0.35             # a mobile number on file
W_HAS_HOME = 0.15             # a landline on file
W_NO_PHONE = -0.35            # no phone number of any kind was provided
W_PHONE_GOOD = 0.20           # client says the number was good at last contact
W_PHONE_BAD = -0.50           # known bad, disconnected or wrong number
W_ADDRESS_GOOD = 0.25         # client says the address was good
W_ADDRESS_BAD = -0.40         # known bad, mail already returned
W_NO_ADDRESS = -0.45          # no address was provided at all
W_CLIENT_LIFT = 1.00          # scale on each client's own lift, from CLIENT_SPECS

PROPENSITY_NOISE_SD = 0.85    # keeps the ceiling realistic; a perfect model is not possible

# Residual effect of what the debt is for, once balance is already accounted for.
# Small utility and telecom balances get paid; deficiency and student paper does not.
PRODUCT_PROPENSITY = {
    "UTILITY": 0.35, "TELECOM": 0.30, "MEDICAL": 0.25, "DENTAL": 0.15,
    "VETERINARY": 0.15, "GYM_MEMBERSHIP": 0.10, "RETAIL_CARD": 0.05,
    "CREDIT_CARD": 0.00, "PERSONAL_LOAN": -0.15, "RENTAL": -0.20,
    "SUBROGATION": -0.25, "AUTO_DEFICIENCY": -0.35, "STUDENT_LOAN": -0.40,
}

# Most of what an account will ever pay arrives in the first few months, so a
# freshly placed account has not had time to show what it is worth.
LIQUIDATION_TIME_CONSTANT_DAYS = 165

# How placements are aged. Primary paper is fresh off charge-off; tertiary paper
# has already been worked by two other agencies and is years old.
PLACEMENT_STAGES = [("PRIMARY", 0.55, 45, 240), ("SECONDARY", 0.27, 300, 800),
                    ("TERTIARY", 0.18, 850, 1800)]


def sigmoid(z):
    return 1.0 / (1.0 + math.exp(-z))


def exposure(days_on_book):
    """The share of an account's lifetime propensity that has had time to appear."""
    return 1.0 - math.exp(-max(0, days_on_book) / LIQUIDATION_TIME_CONSTANT_DAYS)


PHONE_BAD_STATUSES = ("BAD", "DISCONNECTED", "WRONG_NUMBER")


def propensity(debt_age_days, balance, client_paid_days_ago, product, client_lift,
               has_cell, has_home, phone_status, address_status):
    """Latent probability that this account ever pays anything."""
    z = PROPENSITY_INTERCEPT
    z += W_DEBT_AGE * (debt_age_days / 365.25)
    z += W_LOG_BALANCE * math.log10(max(balance, 25.0) / 250.0)
    if client_paid_days_ago is not None:
        z += W_CLIENT_PAID
        z += W_CLIENT_PAID_RECENCY * max(0.0, 1.0 - client_paid_days_ago / 730.0)
    z += PRODUCT_PROPENSITY.get(product, 0.0)
    z += W_CLIENT_LIFT * client_lift

    # Phones
    z += W_HAS_CELL * has_cell + W_HAS_HOME * has_home
    if phone_status == "NONE":
        z += W_NO_PHONE
    elif phone_status in PHONE_BAD_STATUSES:
        z += W_PHONE_BAD
    elif phone_status == "VERIFIED":
        z += W_PHONE_GOOD

    # Address
    if address_status == "NONE":
        z += W_NO_ADDRESS
    elif address_status == "VERIFIED":
        z += W_ADDRESS_GOOD
    elif address_status == "BAD":
        z += W_ADDRESS_BAD

    z += rnd.gauss(0.0, PROPENSITY_NOISE_SD)
    return sigmoid(z)


# What happens when you dial, given what the client told you about the number.
# Multipliers on the base dial-result weights; anything unlisted stays at 1.0.
PHONE_STATUS_DIAL_TILT = {
    "VERIFIED": {"RPC": 1.6, "NO_ANSWER": 0.8, "DISCONNECTED": 0.15, "WRONG_NUMBER": 0.20},
    "UNVERIFIED": {},
    "BAD": {"RPC": 0.35, "NO_ANSWER": 1.3, "DISCONNECTED": 3.0, "WRONG_NUMBER": 2.0},
    "DISCONNECTED": {"RPC": 0.10, "NO_ANSWER": 0.7, "DISCONNECTED": 8.0, "WRONG_NUMBER": 1.0},
    "WRONG_NUMBER": {"RPC": 0.10, "NO_ANSWER": 0.7, "DISCONNECTED": 1.0, "WRONG_NUMBER": 8.0},
    "NONE": {},
}

# How a right party contact tends to go, relative to a propensity of 0.30.
# A consumer who is going to pay promises and pays; one who is not argues.
RPC_TILT = {"PROMISE_TO_PAY": 4.0, "PAYMENT_TAKEN": 4.5, "ARRANGEMENT_SET": 4.0,
            "CALLBACK_SET": 0.3, "REFUSED_TO_PAY": -1.8, "DISPUTE_RAISED": -1.2,
            "HARDSHIP": -0.7, "CEASE_DESIST": -1.3, "ATTORNEY_REP": -0.9}


ACCOUNT_COLUMNS = [
    # System / account identifiers
    "account_id", "client_id", "client_account_number", "original_creditor", "product_type",
    "portfolio_batch", "placement_date", "charge_off_date", "date_of_first_delinquency",
    "account_status", "status_class", "status_date", "closed_date", "close_reason",
    # Money
    "original_balance", "placement_balance", "principal_balance", "interest_accrued",
    "fees_accrued", "adjustment_amount", "current_balance", "total_paid", "interest_rate_pct",
    "last_payment_date", "last_payment_amount",
    "client_last_payment_date", "client_last_payment_amount",
    # Work management
    "assigned_user_id", "last_worked_date", "next_action_date",
    "credit_reported_flag", "created_timestamp", "last_updated_timestamp",
    # Consumer (flattened onto the account row)
    "first_name", "middle_initial", "last_name", "name_suffix", "ssn", "date_of_birth",
    "address_line1", "address_line2", "city", "state", "zip_code", "address_status",
    "phone_home", "phone_cell", "phone_work", "phone_status", "email", "employer_name",
    # Compliance flags
    "do_not_call_flag", "cease_desist_flag", "attorney_represented_flag", "attorney_name",
    "dispute_flag", "dispute_date",
    # Specialized status fields
    "bankruptcy_case_number", "bankruptcy_chapter", "bankruptcy_filed_date", "deceased_date",
]


def build_accounts(clients, users):
    collectors = [u for u in users if u["role"] in ("COLLECTOR", "SR_COLLECTOR", "TEAM_LEAD")]
    active_collectors = [u["user_id"] for u in collectors if u["user_status"] == "ACTIVE"]
    client_pool = [(c, c["_weight"]) for c in clients]
    accounts = []

    for n in range(ACCOUNT_COUNT):
        acct_id = 500001 + n
        client = weighted(client_pool)
        product = weighted(client["_products"])

        # Placements skew toward the recent past; volume has grown over 5 years.
        age_days = int(1826 * (rnd.random() ** 1.35))
        placement = TODAY - timedelta(days=age_days)

        # How stale the paper was when it arrived. This is the debt age feature,
        # and it is deliberately not the same thing as time on book.
        stage = weighted([(s, s[1]) for s in PLACEMENT_STAGES])
        debt_age_days = rnd.randint(stage[2], stage[3])
        charge_off = placement - timedelta(days=debt_age_days)
        dofd = charge_off - timedelta(days=rnd.randint(90, 240))

        low, high = BALANCE_RANGES[product]
        original = skewed_amount(low, high)
        placement_bal = round(original * (1 + rnd.uniform(0.0, 0.08)), 2) if chance(0.35) else original

        # Consumer identity, decided before propensity because contactability feeds it.
        if chance(0.5):
            first = pick(FIRST_NAMES_F)
        else:
            first = pick(FIRST_NAMES_M)
        last = pick(LAST_NAMES)
        city, state, zip5 = pick(CITIES)
        line1, line2 = make_address(state)
        fmt = client["_phone_format"]
        dob = rand_date(date(1945, 1, 1), date(2005, 12, 31))
        dob_str = dob.strftime("%m/%d/%Y") if client["_dob_us_format"] else iso(dob)
        consumer_age = (TODAY - dob).days / 365.25

        # Contact data exactly as the client sent it. Nothing has been skip traced or
        # cleaned up, so a missing or bad address here means the agency genuinely
        # cannot reach this consumer, and the model treats it that way.
        state_out = state
        address_status = weighted([("VERIFIED", 0.55), ("UNVERIFIED", 0.26),
                                   ("BAD", 0.12), ("NONE", 0.07)])
        if address_status == "NONE":
            # Clients express "we have no address" in several different ways.
            shape = weighted([("blank", 0.42), ("literal", 0.24), ("city_only", 0.16),
                              ("po_box", 0.10), ("no_state", 0.08)])
            if shape == "blank":
                line1 = line2 = ""
                city, zip5 = "", ""
            elif shape == "literal":
                line1 = pick(["UNKNOWN", "ADDRESS UNKNOWN", "NO ADDRESS ON FILE", "."])
                line2 = ""
            elif shape == "city_only":
                line1 = line2 = ""
                zip5 = ""
            elif shape == "po_box":
                line1 = f"PO Box {rnd.randint(10, 9999)}"
                line2 = city = ""
            else:
                line1 = line2 = ""
                state_out = ""
                city, zip5 = "", ""

        phone_home = format_phone(state, fmt) if chance(0.55) else ""
        phone_cell = format_phone(state, fmt) if chance(0.82) else ""
        phone_work = format_phone(state, fmt) if chance(0.21) else ""
        if phone_home or phone_cell or phone_work:
            phone_status = weighted([("VERIFIED", 0.40), ("UNVERIFIED", 0.34), ("BAD", 0.11),
                                     ("DISCONNECTED", 0.10), ("WRONG_NUMBER", 0.05)])
        else:
            phone_status = "NONE"

        # Did the consumer ever pay the original creditor, and how long ago?
        client_paid_date = None
        client_paid_amount = 0.0
        if chance(0.42):
            client_paid_date = rand_date(dofd, charge_off)
            client_paid_amount = round(max(10.0, placement_bal * rnd.uniform(0.02, 0.25)), 2)
        client_paid_days_ago = (placement - client_paid_date).days if client_paid_date else None

        # The latent score, and how much of it has had time to show up.
        p_ever = propensity(debt_age_days, placement_bal, client_paid_days_ago, product,
                            client["_lift"], 1 if phone_cell else 0, 1 if phone_home else 0,
                            phone_status, address_status)
        paid_any = chance(p_ever * exposure(age_days))
        resolved = paid_any and chance(0.12 + 0.45 * p_ever)
        settled = resolved and client["allows_settlement"] == "Y" and chance(0.42)
        if resolved:
            paid_frac = 1.0
        elif paid_any:
            # Partial payers pay more of the balance the higher their propensity.
            paid_frac = max(0.02, min(0.85, rnd.betavariate(1.2, 3.0) * (0.7 + 1.6 * p_ever)))
        else:
            paid_frac = 0.0

        # Paying an account off closes it. Otherwise closure is a function of age.
        p_closed = min(0.68, max(0.02, 0.02 + 0.62 * (age_days / 1826)))
        closed = resolved or (age_days >= 25 and chance(p_closed))

        if resolved:
            status = "SETTLED_IN_FULL" if settled else "PAID_IN_FULL"
        elif closed:
            # Bankruptcy tracks balance, death tracks the consumer's age, and the
            # statute runs out on old paper. None of that is about willingness to pay.
            status = weighted([
                ("RETURNED", 0.34), ("RECALLED", 0.11), ("UNCOLLECTIBLE", 0.21),
                ("STATUTE_EXPIRED", 0.08 * (0.2 + 2.0 * min(1.0, debt_age_days / 1800))),
                ("BANKRUPTCY", 0.18 * (0.5 + 1.5 * min(1.0, placement_bal / 8000))),
                ("DECEASED", 0.08 * (0.3 + 2.5 * max(0.0, (consumer_age - 45) / 45))),
            ])
        elif paid_any:
            status = weighted([("PAYMENT_PLAN", 0.42), ("PAYMENT_PLAN_AT_RISK", 0.16),
                               ("PROMISE_TO_PAY", 0.22), ("ACTIVE", 0.20)])
        elif age_days < 25:
            status = "NEW" if chance(0.8) else "ACTIVE"
        else:
            # An account nobody can reach ends up in skip tracing; a big one ends up in legal.
            reachable = bool(phone_cell or phone_home) and address_status != "BAD"
            skip_tilt = 0.5 if reachable else 2.6
            status = weighted([
                ("ACTIVE", 0.38), ("SKIP_TRACE", 0.16 * skip_tilt), ("SKIP_NO_HIT", 0.07 * skip_tilt),
                ("DISPUTED", 0.09), ("LEGAL", 0.07 * (0.2 + 1.8 * min(1.0, placement_bal / 3000))),
                ("CLIENT_HOLD", 0.03), ("HARDSHIP_REVIEW", 0.03), ("MILITARY_SCRA", 0.012),
                ("PENDING_CLIENT_REVIEW", 0.06), ("NEW", 0.05 if age_days < 60 else 0.0),
            ])

        if closed:
            closed_date = rand_date(placement + timedelta(days=18), TODAY)
            status_date = closed_date
        else:
            closed_date = None
            status_date = rand_date(placement, TODAY)
            if chance(0.6):
                status_date = rand_date(max(placement, TODAY - timedelta(days=120)), TODAY)

        acct = {
            "account_id": acct_id,
            "client_id": client["client_id"],
            "client_account_number": (client["_prefix"] +
                                      "".join(str(rnd.randint(0, 9)) for _ in range(client["_digits"]))),
            "original_creditor": client["client_name"],
            "product_type": product,
            "portfolio_batch": f"{placement.year}-{placement.month:02d}-{client['client_code']}",
            "placement_date": iso(placement),
            "charge_off_date": iso(charge_off),
            "date_of_first_delinquency": iso(dofd),
            "account_status": status,
            "status_class": STATUS_CLASS[status],
            "status_date": iso(status_date),
            "closed_date": iso(closed_date),
            "close_reason": CLOSE_REASONS.get(status, "") if closed else "",
            "original_balance": money(original),
            "placement_balance": money(placement_bal),
            "interest_rate_pct": client["interest_rate_pct"],
            "assigned_user_id": str(pick(active_collectors)),
            "last_worked_date": "",
            "next_action_date": "",
            "credit_reported_flag": "Y" if (chance(0.18) and product in ("CREDIT_CARD", "RETAIL_CARD", "PERSONAL_LOAN")) else "N",
            "created_timestamp": ts(business_dt(placement, 6, 23)),
            "last_updated_timestamp": ts(business_dt(status_date, 6, 23)),
            "first_name": first,
            "middle_initial": pick(MIDDLE_INITIALS) if chance(0.55) else "",
            "last_name": last,
            "name_suffix": pick(SUFFIXES) if chance(0.04) else "",
            "ssn": make_ssn(client["_ssn_dashes"]) if chance(0.93) else "",
            "date_of_birth": dob_str if chance(0.96) else "",
            "address_line1": line1, "address_line2": line2,
            "city": city, "state": state_out, "zip_code": zip5,
            "address_status": address_status, "phone_status": phone_status,
            "phone_home": phone_home, "phone_cell": phone_cell, "phone_work": phone_work,
            "email": "",
            "employer_name": pick(EMPLOYERS) if chance(0.58) else "",
            "do_not_call_flag": "N", "cease_desist_flag": "N",
            "attorney_represented_flag": "N", "attorney_name": "",
            "dispute_flag": "N", "dispute_date": "",
            "bankruptcy_case_number": "", "bankruptcy_chapter": "", "bankruptcy_filed_date": "",
            "deceased_date": "",
            # Internal scratch, dropped before writing.
            "client_last_payment_date": iso(client_paid_date),
            "client_last_payment_amount": money(client_paid_amount) if client_paid_date else "",
            "_client": client, "_placement": placement, "_closed_date": closed_date,
            "_status_date": status_date, "_placement_bal": placement_bal, "_age_days": age_days,
            "_phone_fmt": fmt, "_p_ever": p_ever, "_paid_any": paid_any, "_resolved": resolved,
            "_settled": settled, "_paid_frac": paid_frac, "_debt_age_days": debt_age_days,
        }

        if chance(0.72):
            acct["email"] = f"{first.lower()}.{last.lower()}{rnd.randint(1, 99)}@{pick(EMAIL_DOMAINS)}"

        # Compliance flags, correlated with status where that makes sense.
        if chance(0.05):
            acct["do_not_call_flag"] = "Y"
        if chance(0.025):
            acct["cease_desist_flag"] = "Y"
        if status == "LEGAL" or chance(0.03):
            if chance(0.55):
                acct["attorney_represented_flag"] = "Y"
                acct["attorney_name"] = f"{pick(LAST_NAMES)} & {pick(LAST_NAMES)} LLP"
        if status == "DISPUTED":
            acct["dispute_flag"] = "Y"
            acct["dispute_date"] = iso(rand_date(placement, status_date))
        elif chance(0.04):
            acct["dispute_flag"] = "Y"
            acct["dispute_date"] = iso(rand_date(placement, TODAY))

        # Specialized fields, populated only for their matching status.
        if status == "BANKRUPTCY":
            filed = rand_date(placement, closed_date)
            acct["bankruptcy_filed_date"] = iso(filed)
            acct["bankruptcy_chapter"] = weighted([("7", 0.62), ("13", 0.35), ("11", 0.03)])
            acct["bankruptcy_case_number"] = f"{str(filed.year)[2:]}-{rnd.randint(10000, 99999)}-{pick(BK_DISTRICTS)}"
        if status == "DECEASED":
            acct["deceased_date"] = iso(rand_date(placement, closed_date))

        accounts.append(acct)
    return accounts


# --------------------------------------------------------------------------
# Payments and arrangements
# --------------------------------------------------------------------------

PAYMENT_COLUMNS = ["payment_id", "account_id", "arrangement_id", "payment_date", "posted_date",
                   "payment_amount", "payment_method", "payment_type", "payment_status",
                   "reversal_date", "reversal_reason", "check_number", "transaction_reference",
                   "applied_to_principal", "applied_to_interest", "applied_to_fees",
                   "agency_fee_amount", "client_remit_amount", "remit_date",
                   "received_by_user_id", "batch_id"]

ARRANGEMENT_COLUMNS = ["arrangement_id", "account_id", "created_date", "created_by_user_id",
                       "approved_by_user_id", "arrangement_type", "arrangement_status",
                       "total_amount", "down_payment_amount", "installment_amount",
                       "number_of_installments", "payment_frequency", "first_payment_date",
                       "next_payment_date", "final_payment_date", "payments_made",
                       "payments_missed", "amount_paid_to_date", "balance_remaining",
                       "payment_method_on_file", "auto_debit_flag", "broken_date",
                       "broken_reason", "settlement_pct", "last_updated_timestamp"]

METHODS = [("ACH", 0.30), ("DEBIT_CARD", 0.26), ("CREDIT_CARD", 0.16), ("CHECK", 0.12),
           ("MONEY_ORDER", 0.08), ("WESTERN_UNION", 0.04), ("CASH", 0.02), ("ONLINE_PORTAL", 0.02)]

FREQUENCIES = [("MONTHLY", 0.58), ("BIWEEKLY", 0.24), ("WEEKLY", 0.13), ("SEMIMONTHLY", 0.05)]
FREQ_DAYS = {"MONTHLY": 30, "BIWEEKLY": 14, "WEEKLY": 7, "SEMIMONTHLY": 15}


def payment_plan_for(acct):
    """
    How many payments an account made and what they add up to.

    The decision itself was already made in build_accounts from the latent
    propensity; this only turns that outcome into a schedule. Higher propensity
    accounts pay more often as well as more, which is what makes "has already
    paid once" such a strong predictor of paying again.
    """
    if not acct["_paid_any"]:
        return 0, 0.0, 0.0

    total_due = acct["_total_due"]
    p = acct["_p_ever"]
    frac = acct["_paid_frac"]
    adjustment = 0.0

    if acct["_resolved"] and acct["_settled"]:
        floor = int(acct["_client"]["min_settlement_pct"]) / 100.0
        # A few settlements were approved under the client's contractual floor (defect A27).
        pct = rnd.uniform(0.15, floor - 0.05) if acct.get("_under_settle") else rnd.uniform(floor, 0.95)
        target = round(total_due * pct, 2)
        adjustment = round(target - total_due, 2)
    elif acct["_resolved"]:
        target = total_due
    else:
        target = round(min(total_due * frac, total_due), 2)

    if acct["_resolved"]:
        # A payoff is usually a single payment, occasionally a short run of them.
        n = weighted([(1, 0.34), (2, 0.19), (3, 0.13), (4, 0.10), (6, 0.09),
                      (8, 0.07), (12, 0.05), (18, 0.03)])
    else:
        n = int(round(1 + 12 * min(1.0, frac) * (0.4 + 0.9 * p) * rnd.uniform(0.6, 1.4)))
    return max(1, min(24, n)), target, adjustment


def build_money(accounts, users):
    """Fill in balances, then generate payments and arrangements consistently."""
    staff = [u["user_id"] for u in users if u["role"] in ("COLLECTOR", "SR_COLLECTOR", "TEAM_LEAD", "SUPERVISOR")]
    payments, arrangements = [], []
    pay_id, arr_id = 9000001, 700001

    # Pick the settlements that will be approved below the client's floor.
    settled = [a for a in accounts if a["account_status"] == "SETTLED_IN_FULL"]
    rnd.shuffle(settled)
    for a in settled[:20]:
        a["_under_settle"] = True
    record("A27", "accounts", "total_paid, adjustment_amount",
           "Settlements accepted for less than the client's contractual min_settlement_pct. The account "
           "was closed as SETTLED_IN_FULL and the rest of the balance waived without authority.",
           [a["account_id"] for a in settled[:20]],
           "Easiest to see as payment_arrangements.settlement_pct below clients.min_settlement_pct; "
           "otherwise compare total_paid against placement_balance + interest + fees.")

    for acct in accounts:
        client = acct["_client"]
        placement = acct["_placement"]
        end_date = acct["_closed_date"] or TODAY
        years = max(0.0, (end_date - placement).days / 365.25)

        interest = round(acct["_placement_bal"] * (float(client["interest_rate_pct"]) / 100.0)
                         * min(years, 3.0), 2) if client["_interest"] else 0.0
        fees = round(acct["_placement_bal"] * rnd.uniform(0.05, 0.18), 2) if client["_fee"] else 0.0
        if acct["account_status"] == "LEGAL" and chance(0.6):
            fees = round(fees + rnd.choice([65.0, 95.0, 125.0, 210.0]), 2)   # court costs
        acct["_total_due"] = round(acct["_placement_bal"] + interest + fees, 2)

        n_payments, target_paid, adjustment = payment_plan_for(acct)
        acct["_net_paid_target"] = target_paid
        acct["_payments"] = []

        # An arrangement backs most multi-payment accounts.
        arrangement_id = ""
        wants_arrangement = (acct["account_status"] in PLAN_STATUSES
                             or (n_payments >= 2 and chance(0.55))
                             or (acct["account_status"] in ("PAID_IN_FULL", "SETTLED_IN_FULL") and chance(0.5))
                             or (acct["account_status"] in ("ACTIVE", "SKIP_TRACE", "SKIP_NO_HIT")
                                 and chance(0.06)))

        applied_p = applied_i = applied_f = 0.0
        net_paid = 0.0
        last_pay_date = None
        last_pay_amt = 0.0

        if n_payments > 0 and target_paid > 0:
            first_pay = rand_date(placement + timedelta(days=3), max(placement + timedelta(days=10), end_date))
            gap = max(7, int(((end_date - first_pay).days or 30) / max(1, n_payments)))
            per = round(target_paid / n_payments, 2)
            for k in range(n_payments):
                pdate = first_pay + timedelta(days=gap * k + rnd.randint(-3, 3))
                if pdate > TODAY:
                    pdate = TODAY - timedelta(days=rnd.randint(1, 20))
                if pdate < placement:
                    pdate = placement + timedelta(days=2)
                # Never before placement, never after the account closed, never in the future.
                pdate = min(max(pdate, placement), end_date)
                amt = per if k < n_payments - 1 else round(target_paid - per * (n_payments - 1), 2)
                if amt <= 0:
                    continue
                method = weighted(METHODS)
                status = weighted([("POSTED", 0.93), ("NSF_RETURNED", 0.05), ("REVERSED", 0.02)])
                # A paid-off account's payments all have to stick.
                if acct["account_status"] in ("PAID_IN_FULL", "SETTLED_IN_FULL"):
                    status = "POSTED"
                posted = pdate + timedelta(days=rnd.choice([0, 0, 1, 1, 2, 3]))
                rev_date = posted + timedelta(days=rnd.randint(2, 12)) if status != "POSTED" else None

                # Waterfall: fees, then interest, then principal.
                a_f = a_i = a_p = 0.0
                if status == "POSTED":
                    rem = amt
                    a_f = min(rem, max(0.0, fees - applied_f)); rem -= a_f
                    a_i = min(rem, max(0.0, interest - applied_i)); rem -= a_i
                    a_p = round(rem, 2)
                    applied_f += a_f; applied_i += a_i; applied_p += a_p
                    net_paid += amt
                    if last_pay_date is None or pdate > last_pay_date:
                        last_pay_date, last_pay_amt = pdate, amt

                fee_pct = float(client["contingency_rate_pct"]) / 100.0
                agency_fee = round(amt * fee_pct, 2) if status == "POSTED" else 0.0
                payments.append({
                    "payment_id": pay_id, "account_id": acct["account_id"], "arrangement_id": "",
                    "payment_date": iso(pdate), "posted_date": iso(posted),
                    "payment_amount": money(amt), "payment_method": method,
                    "payment_type": ("SETTLEMENT_PAYMENT" if acct["account_status"] == "SETTLED_IN_FULL"
                                     else "ARRANGEMENT_PAYMENT" if wants_arrangement else "PAYMENT"),
                    "payment_status": status,
                    "reversal_date": iso(rev_date),
                    "reversal_reason": "" if status == "POSTED" else ("NSF - INSUFFICIENT FUNDS"
                                                                      if status == "NSF_RETURNED"
                                                                      else pick(["CHARGEBACK", "AGENCY ERROR", "DUPLICATE POSTING"])),
                    "check_number": str(rnd.randint(1000, 9999)) if method in ("CHECK", "MONEY_ORDER") else "",
                    "transaction_reference": f"TXN{rnd.randint(10**9, 10**10 - 1)}",
                    "applied_to_principal": money(a_p), "applied_to_interest": money(a_i),
                    "applied_to_fees": money(a_f),
                    "agency_fee_amount": money(agency_fee),
                    "client_remit_amount": money(round(amt - agency_fee, 2)) if status == "POSTED" else money(0.0),
                    "remit_date": iso(posted + timedelta(days=rnd.randint(5, 20))) if status == "POSTED" else "",
                    "received_by_user_id": str(pick(staff)) if method != "ONLINE_PORTAL" else "1001",
                    "batch_id": f"B{posted.strftime('%Y%m%d')}-{rnd.randint(1, 9)}",
                    "_date": pdate, "_status": status, "_amount": amt, "_method": method,
                })
                acct["_payments"].append(payments[-1])
                pay_id += 1

        if wants_arrangement:
            arr_status_pool = {
                "PAYMENT_PLAN": [("ACTIVE", 0.85), ("BROKEN", 0.15)],
                "PAYMENT_PLAN_AT_RISK": [("ACTIVE", 0.55), ("BROKEN", 0.45)],
                "PAID_IN_FULL": [("COMPLETED", 1.0)],
                "SETTLED_IN_FULL": [("COMPLETED", 1.0)],
            }.get(acct["account_status"], [("BROKEN", 0.62), ("CANCELLED", 0.20), ("COMPLETED", 0.18)])
            arr_status = weighted(arr_status_pool)
            created = (acct["_payments"][0]["_date"] - timedelta(days=rnd.randint(1, 12))
                       if acct["_payments"] else rand_date(placement, end_date))
            if created < placement:
                created = placement + timedelta(days=1)
            freq = weighted(FREQUENCIES)
            made = len([p for p in acct["_payments"] if p["_status"] == "POSTED"])
            n_inst = rnd.choice([3, 4, 6, 6, 8, 10, 12, 12, 18, 24])
            if arr_status == "COMPLETED":
                # A plan that never took a payment was cancelled, not completed.
                arr_status = "COMPLETED" if made else "CANCELLED"
            if arr_status == "COMPLETED":
                n_inst = max(1, made)              # a completed plan ran exactly as long as it paid
            arr_total = (round(acct["_net_paid_target"], 2)
                         if acct["account_status"] == "SETTLED_IN_FULL" else acct["_total_due"])
            inst_amt = round(arr_total / n_inst, 2)
            down = round(inst_amt, 2) if chance(0.25) else 0.0
            first_due = created + timedelta(days=rnd.randint(5, 30))
            missed = max(0, min(n_inst - made, rnd.randint(0, 3) if arr_status != "COMPLETED" else 0))
            paid_to_date = round(sum(p["_amount"] for p in acct["_payments"] if p["_status"] == "POSTED"), 2)
            next_due = first_due + timedelta(days=FREQ_DAYS[freq] * max(made, 1))
            if arr_status == "ACTIVE":
                # A plan that is genuinely active has its next installment still ahead of it.
                while next_due < TODAY:
                    next_due += timedelta(days=FREQ_DAYS[freq])
            broken_date = (next_due + timedelta(days=rnd.randint(5, 45))) if arr_status == "BROKEN" else None
            if broken_date and broken_date > TODAY:
                broken_date = TODAY - timedelta(days=rnd.randint(1, 30))
            arrangement_id = arr_id
            arrangements.append({
                "arrangement_id": arr_id, "account_id": acct["account_id"],
                "created_date": iso(created), "created_by_user_id": str(pick(staff)),
                "approved_by_user_id": str(pick(staff)) if chance(0.4) else "",
                "arrangement_type": ("SETTLEMENT" if acct["account_status"] == "SETTLED_IN_FULL"
                                     else pick(["INSTALLMENT", "INSTALLMENT", "INSTALLMENT", "POST_DATED", "PIF_SCHEDULED"])),
                "arrangement_status": arr_status,
                "total_amount": money(arr_total), "down_payment_amount": money(down),
                "installment_amount": money(inst_amt), "number_of_installments": str(n_inst),
                "payment_frequency": freq, "first_payment_date": iso(first_due),
                "next_payment_date": iso(next_due) if arr_status == "ACTIVE" else "",
                "final_payment_date": iso(first_due + timedelta(days=FREQ_DAYS[freq] * n_inst)),
                "payments_made": str(made), "payments_missed": str(missed),
                "amount_paid_to_date": money(paid_to_date),
                "balance_remaining": money(max(0.0, round(arr_total - paid_to_date, 2))),
                "payment_method_on_file": acct["_payments"][0]["_method"] if acct["_payments"] else pick(["ACH", "DEBIT_CARD"]),
                "auto_debit_flag": "Y" if chance(0.45) else "N",
                "broken_date": iso(broken_date),
                "broken_reason": (pick(["MISSED SCHEDULED PAYMENT", "NSF - PAYMENT RETURNED",
                                        "CONSUMER CANCELLED AUTHORIZATION", "NO CONTACT AFTER MISSED PAYMENT"])
                                  if arr_status == "BROKEN" else ""),
                "settlement_pct": (str(round(arr_total / acct["_total_due"] * 100))
                                   if acct["account_status"] == "SETTLED_IN_FULL" and acct["_total_due"] else ""),
                "last_updated_timestamp": ts(business_dt(broken_date or next_due if (broken_date or next_due) <= TODAY else TODAY)),
                "_created": created, "_status": arr_status, "_freq": freq,
                "_inst_amt": inst_amt, "_n_inst": n_inst,
            })
            for p in acct["_payments"]:
                p["arrangement_id"] = str(arr_id)
            acct["_arrangement"] = arrangements[-1]
            arr_id += 1
        else:
            acct["_arrangement"] = None

        # Settlements and hardship write-offs waive the remainder.
        if acct["account_status"] == "PAID_IN_FULL":
            adjustment = 0.0
            net_paid = acct["_total_due"]
        elif acct["account_status"] == "SETTLED_IN_FULL":
            adjustment = round(net_paid - acct["_total_due"], 2)

        current = round(acct["_total_due"] - net_paid + adjustment, 2)
        if acct["account_status"] in ("PAID_IN_FULL", "SETTLED_IN_FULL"):
            current = 0.0
        current = max(0.0, current)

        acct["principal_balance"] = money(max(0.0, round(acct["_placement_bal"] - applied_p + min(0.0, adjustment), 2)))
        acct["interest_accrued"] = money(interest)
        acct["fees_accrued"] = money(fees)
        acct["adjustment_amount"] = money(adjustment)
        acct["current_balance"] = money(current)
        acct["total_paid"] = money(round(net_paid, 2))
        acct["last_payment_date"] = iso(last_pay_date)
        acct["last_payment_amount"] = money(last_pay_amt) if last_pay_date else ""
        acct["_net_paid"] = net_paid

        # Work-management dates follow from the status.
        if acct["_closed_date"]:
            acct["last_worked_date"] = iso(rand_date(max(placement, acct["_closed_date"] - timedelta(days=30)), acct["_closed_date"]))
            acct["next_action_date"] = ""
        else:
            lw = rand_date(max(placement, TODAY - timedelta(days=90)), TODAY)
            acct["last_worked_date"] = iso(lw)
            acct["next_action_date"] = iso(TODAY + timedelta(days=rnd.randint(1, 45))) if chance(0.8) else ""

    return payments, arrangements


# --------------------------------------------------------------------------
# Notes
# --------------------------------------------------------------------------

NOTE_COLUMNS = ["note_id", "account_id", "note_datetime", "user_id", "contact_type", "action_code",
                "result_code", "phone_dialed", "follow_up_date", "is_system_generated", "note_text"]

RELATIONS = ["spouse", "the consumer's mother", "a roommate", "the consumer's brother",
             "an unidentified female", "an unidentified male", "the consumer's daughter"]

DIAL_RESULTS = [
    ("NO_ANSWER", 0.30, "Dialed {phone}. No answer, no voicemail box configured."),
    ("LEFT_MESSAGE", 0.22, "Dialed {phone}. Reached voicemail; left approved message with callback number and mini-Miranda."),
    ("BUSY", 0.06, "Dialed {phone}. Line busy, will retry next cycle."),
    ("DISCONNECTED", 0.07, "Dialed {phone}. Recording states number is disconnected or no longer in service. Removed from dialer."),
    ("WRONG_NUMBER", 0.06, "Dialed {phone}. Party answering states this is not the consumer and they do not know them. Number scrubbed."),
    ("TPC", 0.07, "Dialed {phone}. Spoke with {relation}. Did not disclose the nature of the call, left name and callback number only."),
    ("HUNG_UP", 0.04, "Dialed {phone}. Party hung up immediately after the greeting."),
    ("RPC", 0.18, None),
]

RPC_OUTCOMES = [
    ("PROMISE_TO_PAY", 0.15,
     "RPC with consumer, identity verified with date of birth and last four of SSN. Reviewed balance of ${bal}. "
     "Consumer committed to pay ${amt} on {fdate}. Confirmation letter requested."),
    ("REFUSED_TO_PAY", 0.22,
     "RPC with consumer. Consumer states they will not pay, \"this bill is not mine and I never signed anything.\" "
     "Advised of validation rights. No further commitment obtained."),
    ("HARDSHIP", 0.13,
     "RPC with consumer. Reports reduced hours at {employer} and is behind on rent. Requested hardship review; "
     "gathering income documentation before any arrangement is set."),
    ("DISPUTE_RAISED", 0.12,
     "RPC with consumer. Consumer disputes the balance, states the account was paid directly to {creditor} "
     "before placement. Dispute logged, collection activity suspended pending validation."),
    ("PAYMENT_TAKEN", 0.07,
     "RPC with consumer. Took payment of ${amt} by {method} over the phone. Receipt emailed at consumer request."),
    ("ARRANGEMENT_SET", 0.05,
     "RPC with consumer. Negotiated {n} {freq} installments of ${inst} beginning {fdate}. Terms read back and accepted."),
    ("CALLBACK_SET", 0.14,
     "RPC with consumer. Consumer states they are at work and cannot talk. Callback scheduled for {fdate}."),
    ("CEASE_DESIST", 0.05,
     "RPC with consumer. Consumer stated, \"stop calling me, I do not want to hear from you again.\" "
     "Cease and desist request documented."),
    ("ATTORNEY_REP", 0.03,
     "RPC with consumer. Consumer advises they are represented by counsel, {attorney}, regarding this debt. "
     "Ended call, no further direct contact."),
    ("BK_NOTICE", 0.02,
     "RPC with consumer. Consumer states they filed bankruptcy and gave a case number. Routed to the bankruptcy desk for verification."),
    ("DECEASED_NOTICE", 0.01,
     "Inbound contact from a family member advising the consumer is deceased. Requested a copy of the death certificate."),
]

LETTER_NOTES = [
    "Validation notice generated and mailed to the address on file. 30-day dispute window opens on delivery.",
    "Second notice mailed. No response to the initial validation letter.",
    "Settlement offer letter mailed at {pct}% of the current balance. Offer expires {fdate}.",
    "Pre-legal review letter mailed. Account meets the client's suit placement threshold.",
    "Mail returned by USPS marked \"Attempted - Not Known.\" Address flagged as bad, account routed to skip trace.",
    "Annual statement of account mailed per client requirement.",
]

EMAIL_NOTES = [
    "Email sent to {email} with the current balance and the online payment portal link.",
    "Email bounced, mailbox does not exist. Email address flagged invalid.",
    "Consumer opened the payment portal link from the emailed reminder but did not complete a transaction.",
    "Emailed a copy of the itemization received from the client at the consumer's request.",
]

SMS_NOTES = [
    "SMS sent to {phone} per the consent on file: balance reminder and callback request.",
    "SMS delivery failed, carrier reports the number is not text enabled.",
    "Consumer replied STOP to the text message. Number removed from the SMS campaign.",
]

SKIP_NOTES = [
    "Skip trace request submitted to vendor. Awaiting results.",
    "Skip trace returned a possible new address in {city}, {state}. Sending confirmation letter before dialing.",
    "Skip trace returned no new information. Account remains in skip status.",
    "Credit bureau locate returned an updated employer: {employer}. Work number added to the account.",
    "Social media locate attempted, results inconclusive. No contact information updated.",
]

LEGAL_NOTES = [
    "Account reviewed for legal placement. Balance, documentation and statute all check out.",
    "Suit filed. Case number {case} assigned. Service of process pending.",
    "Consumer served. Answer due within 30 days.",
    "Default judgment entered. Post-judgment interest accruing per state rate.",
    "Garnishment packet prepared and sent to counsel for filing.",
]

COMPLIANCE_NOTES = [
    ("QA_PASSED", "Call recording reviewed by QA. Score {score}/100. No compliance exceptions noted."),
    ("QA_EXCEPTION", "Call recording reviewed by QA. Score {score}/100. Coaching noted for failure to "
                     "re-verify identity before disclosing account details."),
    ("TRAINING_LOGGED", "Annual FDCPA refresher acknowledged by the assigned collector."),
    ("COMPLAINT_LOGGED", "Complaint received through the client portal. Routed to compliance for a "
                         "response within 5 business days."),
]

# Multi-line note bodies: real agents paste structured summaries into the note field.
MULTILINE_NOTES = [
    "Inbound call, consumer summary:\n- Disputes the late fees only, not the principal\n- Will mail bank statements this week\n- Callback set for {fdate}",
    "Consumer budget review:\n  Income: ${inc}/mo\n  Rent: ${rent}/mo\n  Result: cannot commit above ${amt}/mo at this time",
    "Client instruction received:\n1. Suspend dialing for 30 days\n2. Do not report to credit bureaus\n3. Re-review on {fdate}",
]


def build_notes(accounts, users, writer):
    """Stream notes straight to the CSV writer; this is the largest table."""
    collectors = [u for u in users if u["role"] in ("COLLECTOR", "SR_COLLECTOR", "TEAM_LEAD")]
    collector_ids = [u["user_id"] for u in collectors]
    terminated_ids = [u["user_id"] for u in collectors if u["user_status"] == "TERMINATED"]
    compliance_ids = [u["user_id"] for u in users if u["role"] in ("COMPLIANCE", "SUPERVISOR")]
    legal_ids = [u["user_id"] for u in users if u["role"] == "LEGAL_SPECIALIST"] or collector_ids
    SYSTEM_USER = 1001

    note_id = 4000001
    stats = {"total": 0}
    # Pre-selected accounts that receive planted note-level defects.
    idx = list(range(len(accounts)))
    rnd.shuffle(idx)
    bad_user_accts = set(idx[:40])
    early_note_accts = set(idx[40:65])
    odd_hour_accts = set(idx[65:185])
    ghost_cd_accts = set(idx[185:220])
    ghost_atty_accts = set(idx[220:245])
    dupe_note_accts = set(idx[245:295])
    # This one only makes sense on accounts that are genuinely closed.
    closed_idx = [j for j, a in enumerate(accounts)
                  if a["_closed_date"] and a["_closed_date"] < TODAY - timedelta(days=10)]
    rnd.shuffle(closed_idx)
    post_close_accts = set(closed_idx[:30])
    third_party_accts = set(idx[325:340])
    multiline_accts = set(idx[340:400])

    planted = {k: [] for k in ("N1", "N2", "N3", "N4a", "N4b", "N5", "N7", "N8", "N6", "A31")}

    for i, acct in enumerate(accounts):
        placement = acct["_placement"]
        end = acct["_closed_date"] or TODAY
        window = max(1, (end - placement).days)
        assigned = int(acct["assigned_user_id"])
        phones = [p for p in (acct["phone_cell"], acct["phone_home"], acct["phone_work"]) if p]
        events = []

        def add(day, hour_range, user, contact, action, result, text, phone="", follow="", system="N"):
            d = placement + timedelta(days=max(0, min(window, day)))
            when = business_dt(d, *hour_range)
            events.append([when, user, contact, action, result, phone, follow, system, text])

        # --- opening system notes -----------------------------------------
        add(0, (5, 8), SYSTEM_USER, "SYSTEM", "PLACEMENT", "ACCOUNT_LOADED",
            f"Account placed by {acct['original_creditor']} in batch {acct['portfolio_batch']}. "
            f"Placement balance ${acct['placement_balance']}. Charge-off date {acct['charge_off_date']}.",
            system="Y")
        add(rnd.randint(1, 4), (5, 8), SYSTEM_USER, "LETTER", "LETTER_SENT", "VALIDATION_NOTICE",
            LETTER_NOTES[0], system="Y")

        # --- dialing and correspondence activity --------------------------
        n_activity = max(2, int(rnd.gauss(NOTE_ACTIVITY_MEAN, NOTE_ACTIVITY_SD)))
        if acct["account_status"] in ("NEW", "PENDING_CLIENT_REVIEW"):
            n_activity = max(1, int(n_activity * 0.35))
        if acct["account_status"] in ("SKIP_TRACE", "SKIP_NO_HIT", "LEGAL", "PAYMENT_PLAN",
                                      "PAYMENT_PLAN_AT_RISK", "DISPUTED"):
            n_activity = int(n_activity * 1.25)

        for _ in range(n_activity):
            day = rnd.randint(1, window)
            roll = rnd.random()
            user = pick(collector_ids)
            if i in bad_user_accts and chance(0.25):
                user = 9999                       # defect N1: unknown user_id
                planted["N1"].append(acct["account_id"])
            elif chance(0.10) and terminated_ids:
                user = pick(terminated_ids)

            hours = (8, 20)
            if i in odd_hour_accts and chance(0.35):
                hours = pick([(5, 7), (21, 23)])   # defect N3: outside 8am-9pm
                planted["N3"].append(acct["account_id"])

            if roll < 0.62 and phones:
                phone = pick(phones)
                dial_tilt = PHONE_STATUS_DIAL_TILT.get(acct["phone_status"], {})
                result = weighted([(r, w * dial_tilt.get(r, 1.0)) for r, w, _ in DIAL_RESULTS])
                if result == "RPC":
                    # How the conversation goes depends on the same latent propensity
                    # that drives payment, so the notes carry real signal.
                    tilt = acct["_p_ever"] - 0.30
                    outcome = weighted([(o, max(0.005, w * (1.0 + RPC_TILT.get(o, 0.0) * tilt)))
                                        for o, w, _ in RPC_OUTCOMES])
                    if outcome == "PAYMENT_TAKEN" and not acct["_payments"]:
                        outcome = "PROMISE_TO_PAY"      # do not log a payment that never posted
                    template = next(t for o, _, t in RPC_OUTCOMES if o == outcome)
                    follow = ""
                    if outcome in ("PROMISE_TO_PAY", "CALLBACK_SET", "ARRANGEMENT_SET"):
                        follow = iso(placement + timedelta(days=min(window, day + rnd.randint(3, 21))))
                    text = template.format(
                        bal=acct["placement_balance"],
                        amt=money(max(20.0, float(acct["placement_balance"]) * rnd.uniform(0.05, 0.3))),
                        fdate=follow or iso(placement + timedelta(days=min(window, day + 7))),
                        method=weighted(METHODS), employer=acct["employer_name"] or "their employer",
                        creditor=acct["original_creditor"],
                        n=rnd.choice([4, 6, 8, 12]), freq=weighted(FREQUENCIES).lower(),
                        inst=money(max(25.0, float(acct["placement_balance"]) / rnd.choice([6, 8, 12]))),
                        attorney=acct["attorney_name"] or f"{pick(LAST_NAMES)} Law Office")
                    # A documented restriction normally propagates to the account flags.
                    if outcome == "CEASE_DESIST":
                        acct["cease_desist_flag"] = "Y"
                        acct["do_not_call_flag"] = "Y"
                    elif outcome == "ATTORNEY_REP":
                        acct["attorney_represented_flag"] = "Y"
                        if not acct["attorney_name"]:
                            acct["attorney_name"] = f"{pick(LAST_NAMES)} & {pick(LAST_NAMES)} LLP"
                    add(day, hours, user, "OUTBOUND_CALL", "DIAL", outcome, text, phone, follow)
                else:
                    template = next(t for r, _, t in DIAL_RESULTS if r == result)
                    text = template.format(phone=phone, relation=pick(RELATIONS))
                    if result == "TPC" and i in third_party_accts:
                        text = (f"Dialed {phone}. Spoke with {pick(RELATIONS)} and advised we were calling to collect "
                                f"a past due balance of ${acct['placement_balance']} owed to {acct['original_creditor']}. "
                                f"Asked them to pass the message along.")
                        planted["N8"].append(acct["account_id"])
                    add(day, hours, user, "OUTBOUND_CALL", "DIAL", result, text, phone)
            elif roll < 0.72:
                # The validation notice goes out once, at placement; later letters are follow-ups.
                add(day, (6, 9), SYSTEM_USER, "LETTER", "LETTER_SENT", "CORRESPONDENCE",
                    pick(LETTER_NOTES[1:]).format(pct=rnd.choice([50, 55, 60, 65, 70]),
                                                  fdate=iso(placement + timedelta(days=min(window, day + 30)))),
                    system="Y")
            elif roll < 0.80:
                if phones and chance(0.4):
                    add(day, (7, 20), user, "SMS", "SMS_SENT", "CORRESPONDENCE",
                        pick(SMS_NOTES).format(phone=phones[0]))
                else:
                    add(day, (7, 20), user, "EMAIL", "EMAIL_SENT", "CORRESPONDENCE",
                        pick(EMAIL_NOTES).format(email=acct["email"] or "no address on file"))
            elif roll < 0.88 and acct["account_status"] in ("SKIP_TRACE", "SKIP_NO_HIT", "ACTIVE",
                                                           "RETURNED", "UNCOLLECTIBLE"):
                city, state, _ = pick(CITIES)
                add(day, (8, 18), user, "SKIP_TRACE", "SKIP", pick(["SKIP_ORDERED", "SKIP_HIT", "SKIP_NO_HIT"]),
                    pick(SKIP_NOTES).format(city=city, state=state, employer=pick(EMPLOYERS)))
            elif roll < 0.93:
                code, template = pick(COMPLIANCE_NOTES)
                add(day, (8, 18), pick(compliance_ids), "REVIEW", "QA", code,
                    template.format(score=rnd.randint(72, 100)))
            elif roll < 0.97 and acct["account_status"] == "LEGAL":
                add(day, (8, 18), pick(legal_ids), "LEGAL", "LEGAL_ACTION", "LEGAL_UPDATE",
                    pick(LEGAL_NOTES).format(case=f"CV-{placement.year}-{rnd.randint(1000, 9999)}"))
            else:
                add(day, (8, 19), user, "INBOUND_CALL", "DIAL", "RPC",
                    f"Inbound call from consumer. Verified identity and answered questions about the "
                    f"balance of ${acct['placement_balance']}. No commitment obtained.")

        # Defects N4a/N4b: the note documents a contact restriction that the account
        # flags never picked up, so the consumer keeps getting worked.
        if i in ghost_cd_accts:
            day = rnd.randint(1, window)
            add(day, (8, 19), pick(collector_ids), "OUTBOUND_CALL", "DIAL", "CEASE_DESIST",
                "RPC with consumer. Consumer stated, \"stop calling me, I do not want to hear from "
                "you people again, put it in writing.\" Cease and desist request documented.",
                phones[0] if phones else "")
            acct["cease_desist_flag"] = "N"
            acct["do_not_call_flag"] = "N"
            planted["N4a"].append(acct["account_id"])
        if i in ghost_atty_accts:
            day = rnd.randint(1, window)
            add(day, (8, 19), pick(collector_ids), "OUTBOUND_CALL", "DIAL", "ATTORNEY_REP",
                f"RPC with consumer. Consumer advises they are represented by counsel, "
                f"{pick(LAST_NAMES)} & {pick(LAST_NAMES)} LLP, on this debt and asked that all "
                f"further contact go through the firm. Ended the call.",
                phones[0] if phones else "")
            acct["attorney_represented_flag"] = "N"
            acct["attorney_name"] = ""
            planted["N4b"].append(acct["account_id"])

        # Defect N6: free-text notes containing embedded newlines and quotes.
        if i in multiline_accts:
            day = rnd.randint(1, window)
            add(day, (8, 19), pick(collector_ids), "INBOUND_CALL", "DIAL", "RPC",
                pick(MULTILINE_NOTES).format(
                    fdate=iso(placement + timedelta(days=min(window, day + 10))),
                    inc=rnd.randint(1400, 4200), rent=rnd.randint(600, 2200),
                    amt=rnd.choice([25, 40, 50, 75, 100])))
            planted["N6"].append(acct["account_id"])

        # --- payment notes -------------------------------------------------
        for p in acct["_payments"]:
            day = (p["_date"] - placement).days
            if p["_status"] == "POSTED":
                text = (f"Payment of ${money(p['_amount'])} received via {p['_method']}. "
                        f"Reference {p['transaction_reference']}. Posted to the account.")
                result = "PAYMENT_POSTED"
            elif p["_status"] == "NSF_RETURNED":
                text = (f"Payment of ${money(p['_amount'])} returned NSF by the consumer's bank. "
                        f"Balance restored and the arrangement flagged at risk.")
                result = "PAYMENT_NSF"
            else:
                text = f"Payment of ${money(p['_amount'])} reversed. Reason: {p['reversal_reason']}."
                result = "PAYMENT_REVERSED"
            add(day, (6, 22), SYSTEM_USER, "PAYMENT", "PAYMENT", result, text, system="Y")

        # --- arrangement notes ----------------------------------------------
        arr = acct["_arrangement"]
        if arr:
            day = (arr["_created"] - placement).days
            add(day, (8, 19), int(arr["created_by_user_id"]), "ARRANGEMENT", "ARRANGEMENT_SET", "PLAN_CREATED",
                f"Payment arrangement {arr['arrangement_id']} established: {arr['_n_inst']} {arr['_freq'].lower()} "
                f"installments of ${arr['_inst_amt']:.2f} beginning {arr['first_payment_date']}. "
                f"Terms disclosed and accepted by the consumer.")
            if arr["broken_date"]:
                bd = (date.fromisoformat(arr["broken_date"]) - placement).days
                add(bd, (6, 20), SYSTEM_USER, "ARRANGEMENT", "ARRANGEMENT_BROKEN", "PLAN_BROKEN",
                    f"Arrangement {arr['arrangement_id']} broken. Reason: {arr['broken_reason']}. "
                    f"Account returned to active collections.", system="Y")

        # --- status change and closure notes ---------------------------------
        if acct["account_status"] == "BANKRUPTCY":
            add(window - rnd.randint(0, 5), (6, 20), SYSTEM_USER, "SYSTEM", "STATUS_CHANGE", "BK_CONFIRMED",
                f"Bankruptcy verified. Chapter {acct['bankruptcy_chapter']} case {acct['bankruptcy_case_number']} "
                f"filed {acct['bankruptcy_filed_date']}. All collection activity ceased and the account closed.",
                system="Y")
        elif acct["account_status"] == "DECEASED":
            add(window - rnd.randint(0, 5), (6, 20), SYSTEM_USER, "SYSTEM", "STATUS_CHANGE", "DECEASED_CONFIRMED",
                f"Deceased notification confirmed, date of death {acct['deceased_date']}. Account closed; "
                f"any further contact must be directed to the estate representative only.", system="Y")
        elif acct["_closed_date"]:
            add(window, (6, 20), SYSTEM_USER, "SYSTEM", "STATUS_CHANGE", "ACCOUNT_CLOSED",
                f"Account closed. Status set to {acct['account_status']}. Reason: {acct['close_reason']}.", system="Y")

        # Defect N7: collection activity logged after the account was closed.
        if i in post_close_accts and acct["_closed_date"] and acct["_closed_date"] < TODAY - timedelta(days=10):
            after = acct["_closed_date"] + timedelta(days=rnd.randint(5, 60))
            if after > TODAY:
                after = TODAY
            when = business_dt(after)
            phone = phones[0] if phones else "no number on file"
            events.append([when, pick(collector_ids), "OUTBOUND_CALL", "DIAL", "LEFT_MESSAGE",
                           phone, "", "N",
                           f"Dialed {phone}. Left message requesting a return call regarding the balance."])
            planted["N7"].append(acct["account_id"])

        # Defect N2: notes dated before the account was placed.
        if i in early_note_accts:
            when = business_dt(placement - timedelta(days=rnd.randint(3, 40)))
            events.append([when, pick(collector_ids), "OUTBOUND_CALL", "DIAL", "NO_ANSWER",
                           phones[0] if phones else "", "", "N",
                           "Dialed number on file. No answer."])
            planted["N2"].append(acct["account_id"])

        events.sort(key=lambda e: e[0])

        # Defect N5: the interface double-posted a note.
        if i in dupe_note_accts and len(events) > 4:
            dup = list(events[3])
            events.insert(4, dup)
            planted["N5"].append(acct["account_id"])

        if acct["phone_status"] in ("WRONG_NUMBER", "DISCONNECTED"):
            dialed = sum(1 for e in events if e[2] == "OUTBOUND_CALL")
            if dialed >= 6:
                planted["A31"].append((acct["account_id"], dialed))

        for ev in events:
            when, user, contact, action, result, phone, follow, system, text = ev
            writer.writerow([note_id, acct["account_id"], ts(when), user, contact, action,
                             result, phone, follow, system, text])
            note_id += 1
            stats["total"] += 1

    wasted = sorted(planted["A31"], key=lambda t: -t[1])
    record("A31", "accounts", "phone_status",
           "Accounts whose phone the client already flagged as disconnected or a wrong number, "
           "dialed six or more times anyway. Wasted dialer capacity at best, and continuing to "
           "call a number known to belong to someone else is an FDCPA problem.",
           [a for a, _ in wasted],
           f"Worst case here was {wasted[0][1]} outbound calls on one account." if wasted else "")
    record("N1", "notes", "user_id", "Notes written by user_id 9999, which does not exist in users.csv.",
           sorted(set(planted["N1"])), "Left join notes to users on user_id.")
    record("N2", "notes", "note_datetime",
           "Notes dated before the account's placement_date.", sorted(set(planted["N2"])))
    record("N3", "notes", "note_datetime",
           "Outbound call notes timestamped outside 8:00am-9:00pm, an FDCPA calling-window problem.",
           sorted(set(planted["N3"])), "Filter contact_type = OUTBOUND_CALL and check the hour part of note_datetime.")
    record("N4a", "notes", "note_text",
           "Notes documenting a cease and desist request where accounts.cease_desist_flag is still N.",
           sorted(set(planted["N4a"])), "Search note_text for 'cease and desist' and compare the account flag.")
    record("N4b", "notes", "note_text",
           "Notes documenting attorney representation where accounts.attorney_represented_flag is still N.",
           sorted(set(planted["N4b"])))
    record("N5", "notes", "note_text",
           "Exact duplicate notes: same account, timestamp and text under two note_ids.",
           sorted(set(planted["N5"])))
    record("N6", "notes", "note_text",
           "Note text containing embedded newlines, quotes and commas. Correct per RFC 4180 but it "
           "breaks naive line-by-line parsing.", sorted(set(planted["N6"])),
           "notes.csv has far more physical lines than records.")
    record("N7", "notes", "note_datetime",
           "Collection calls logged after the account was closed, including bankruptcy and deceased accounts.",
           sorted(set(planted["N7"])))
    record("N8", "notes", "note_text",
           "Third-party disclosure: the balance and creditor were revealed to someone other than the consumer.",
           sorted(set(planted["N8"])), "A compliance issue rather than a structural one.")
    return note_id, stats["total"]


# --------------------------------------------------------------------------
# Deliberate defects in accounts, payments and arrangements
# --------------------------------------------------------------------------

def corrupt_accounts(accounts, users, clients):
    n = len(accounts)
    valid_user_ids = {u["user_id"] for u in users}
    terminated = [u["user_id"] for u in users if u["user_status"] == "TERMINATED"]

    def sample(k, predicate=None, exclude=None):
        pool = [a for a in accounts if (predicate is None or predicate(a))
                and (exclude is None or a["account_id"] not in exclude)]
        rnd.shuffle(pool)
        return pool[:k]

    used = set()

    # A1 -- addresses the client never provided. This is not corruption; it is what
    # arrived, which is why address_status carries NONE and why these accounts
    # genuinely liquidate worse. The trap is that "no address" is written several
    # different ways, so any count of it has to normalize first.
    targets = [a for a in accounts if a["address_status"] == "NONE"]
    record("A1", "accounts", "address_line1, city, state, zip_code, address_status",
           "Accounts placed with no usable address. Written five different ways: every field "
           "blank, a literal 'UNKNOWN' in address_line1, a city and state with no street, a PO "
           "box with no city, and a street with no state.",
           [a["account_id"] for a in targets],
           "Real signal, not noise. These liquidate materially worse, so treat address_status "
           "NONE as a feature rather than a row to drop.")

    # A2 -- ZIP codes that lost their leading zero somewhere upstream.
    ne = [a for a in accounts if a["zip_code"].startswith("0")]
    rnd.shuffle(ne)
    targets = ne[:int(len(ne) * 0.45)]
    for a in targets:
        a["zip_code"] = a["zip_code"].lstrip("0")
    record("A2", "accounts", "zip_code",
           "Northeast ZIP codes stored with the leading zero stripped (e.g. 2108 instead of 02108).",
           [a["account_id"] for a in targets],
           "Classic spreadsheet round-trip damage. Look for zip_code shorter than 5 characters.")

    # A3 -- state and ZIP that do not belong together.
    targets = sample(35, lambda a: a["zip_code"] and a["state"])
    for a in targets:
        other = pick([c for c in CITIES if c[1] != a["state"]])
        a["zip_code"] = other[2]
    record("A3", "accounts", "state, zip_code", "ZIP code does not fall in the stated state.",
           [a["account_id"] for a in targets])

    # A4 -- balance grew on a client that charges neither interest nor fees.
    targets = sample(40, lambda a: not a["_client"]["_interest"] and not a["_client"]["_fee"]
                     and a["account_status"] not in ("PAID_IN_FULL", "SETTLED_IN_FULL"))
    for a in targets:
        a["current_balance"] = money(round(float(a["placement_balance"]) * rnd.uniform(1.15, 1.9), 2))
    record("A4", "accounts", "current_balance",
           "current_balance exceeds placement_balance on clients whose contract allows no interest and no fees.",
           [a["account_id"] for a in targets],
           "Join accounts to clients on client_id and compare against allows_interest / allows_fees.")

    # A5 -- closed-paid accounts still carrying a balance.
    targets = sample(25, lambda a: a["account_status"] in ("PAID_IN_FULL", "SETTLED_IN_FULL"))
    for a in targets:
        a["current_balance"] = money(round(rnd.uniform(15, 850), 2))
    record("A5", "accounts", "account_status, current_balance",
           "Accounts closed as PAID_IN_FULL or SETTLED_IN_FULL that still show a non-zero balance.",
           [a["account_id"] for a in targets])

    # A6 -- overpayments left as negative balances.
    targets = sample(12, lambda a: float(a["total_paid"]) > 0)
    for a in targets:
        a["current_balance"] = money(-round(rnd.uniform(5, 240), 2))
    record("A6", "accounts", "current_balance", "Negative current_balance from unrefunded overpayments.",
           [a["account_id"] for a in targets])

    # A7 -- bankruptcy status without the bankruptcy detail.
    targets = sample(18, lambda a: a["account_status"] == "BANKRUPTCY")
    for a in targets:
        if chance(0.5):
            a["bankruptcy_case_number"] = ""
        else:
            a["bankruptcy_chapter"] = ""
            if chance(0.4):
                a["bankruptcy_filed_date"] = ""
    record("A7", "accounts", "bankruptcy_case_number, bankruptcy_chapter, bankruptcy_filed_date",
           "BANKRUPTCY accounts missing the case number, chapter or filing date.",
           [a["account_id"] for a in targets],
           "These fields should be fully populated for every BANKRUPTCY account.")
    used |= {a["account_id"] for a in targets}

    # A8 -- bankruptcy data on accounts that are not in bankruptcy status.
    targets = sample(10, lambda a: a["account_status"] in ("ACTIVE", "PAYMENT_PLAN",
                                                          "SKIP_TRACE", "RETURNED"))
    for a in targets:
        filed = rand_date(a["_placement"], TODAY)
        a["bankruptcy_case_number"] = f"{str(filed.year)[2:]}-{rnd.randint(10000, 99999)}-{pick(BK_DISTRICTS)}"
        a["bankruptcy_chapter"] = pick(["7", "13"])
        a["bankruptcy_filed_date"] = iso(filed)
    record("A8", "accounts", "bankruptcy_case_number, account_status",
           "Bankruptcy case data present on accounts whose status is not BANKRUPTCY, so collection activity continued.",
           [a["account_id"] for a in targets],
           "The reverse of A7, and the more dangerous direction.")

    # A9 -- deceased data problems.
    targets = sample(7, lambda a: a["account_status"] == "DECEASED" and a["account_id"] not in used)
    for a in targets:
        a["deceased_date"] = ""
    record("A9a", "accounts", "deceased_date", "DECEASED accounts with no date of death recorded.",
           [a["account_id"] for a in targets])
    used |= {a["account_id"] for a in targets}
    targets = sample(5, lambda a: a["account_status"] == "DECEASED" and a["account_id"] not in used)
    for a in targets:
        a["deceased_date"] = iso(a["_placement"] - timedelta(days=rnd.randint(30, 900)))
    record("A9b", "accounts", "deceased_date, placement_date",
           "Date of death precedes the placement date; the account should never have been placed.",
           [a["account_id"] for a in targets])

    # A10 -- impossible dates of birth.
    targets = sample(8, lambda a: a["date_of_birth"])
    for a in targets:
        d = TODAY - timedelta(days=rnd.randint(2000, 6400))       # a minor
        a["date_of_birth"] = d.strftime("%m/%d/%Y") if a["_client"]["_dob_us_format"] else iso(d)
    record("A10a", "accounts", "date_of_birth", "Date of birth implies the consumer is under 18.",
           [a["account_id"] for a in targets])
    targets = sample(6, lambda a: a["date_of_birth"])
    for a in targets:
        d = date(rnd.randint(1899, 1912), rnd.randint(1, 12), rnd.randint(1, 28))
        a["date_of_birth"] = d.strftime("%m/%d/%Y") if a["_client"]["_dob_us_format"] else iso(d)
    record("A10b", "accounts", "date_of_birth", "Date of birth implies an age over 110.",
           [a["account_id"] for a in targets])

    # A11 -- placeholder and malformed junk typed into the SSN field.
    targets = sample(20, lambda a: a["ssn"])
    for a in targets:
        # Every one of these is either unissuable or the wrong shape entirely.
        # 987-65-4321 sits in the SSA advertising block, and 666 / 999 area
        # numbers have never been issued, so nothing here can belong to a person.
        bad = pick(["000-00-0000", "666-66-6666", "987-65-4321", "999-99-9999",
                    "XXX-XX-4417", "UNKNOWN", "N/A", "12345678", "555-12-34567", "0"])
        a["ssn"] = bad if "-" in a["ssn"] or not bad.replace("-", "").isdigit() else bad.replace("-", "")
    record("A11", "accounts", "ssn",
           "Placeholder and malformed junk in the SSN field: all zeros, repeated digits, sequential "
           "digits, masked values, free text, and values that are not nine digits.",
           [a["account_id"] for a in targets],
           "Every SSN in this file is deliberately unissuable, so these stand out by being the wrong "
           "shape rather than by being invalid.")

    # A12 -- one SSN shared by consumers with different names.
    shared = make_ssn(True)
    targets = sample(14, lambda a: a["ssn"])
    for a in targets:
        a["ssn"] = shared if "-" in a["ssn"] else shared.replace("-", "")
    record("A12", "accounts", "ssn",
           f"Fourteen accounts with different consumer names share a single SSN ({shared}).",
           [a["account_id"] for a in targets],
           "Group by ssn and count distinct last_name.")

    # A13 -- unusable phone numbers.
    targets = sample(60, lambda a: a["phone_cell"] or a["phone_home"])
    for a in targets:
        bad = pick(["0000000000", "999-999-9999", "555-1234", "(000) 000-0000", "1234567",
                    "NONE", "no phone", "111-111-1111"])
        if a["phone_cell"]:
            a["phone_cell"] = bad
        else:
            a["phone_home"] = bad
    record("A13", "accounts", "phone_home, phone_cell",
           "Placeholder or malformed phone numbers, plus four different phone formats across the file "
           "depending on which client sent the account.",
           [a["account_id"] for a in targets],
           "The formatting inconsistency is by client_id; the junk values are scattered.")

    # A14 -- unusable email addresses.
    targets = sample(90, lambda a: a["email"])
    for a in targets:
        a["email"] = pick(["none", "N/A", "no email", "notanemail.com", "consumer@", "@gmail.com",
                           "test@test", "unknown@unknown.com", "x@x.x", "NULL"])
    record("A14", "accounts", "email", "Invalid or placeholder email addresses.",
           [a["account_id"] for a in targets])

    # A15 -- the same debt placed twice under two account_ids.
    sources = sample(22, lambda a: a["account_status"] not in CLOSED_SET)
    dupes = sample(22, lambda a: a["account_id"] not in {s["account_id"] for s in sources})
    pairs = []
    for src, dst in zip(sources, dupes):
        for field in ("client_id", "client_account_number", "original_creditor", "product_type",
                      "first_name", "middle_initial", "last_name", "ssn", "date_of_birth",
                      "address_line1", "address_line2", "city", "state", "zip_code",
                      "original_balance", "placement_balance"):
            dst[field] = src[field]
        # The duplicate keeps its own placement date and history; only the debt is the same.
        if chance(0.5):
            dst["current_balance"] = money(round(float(src["current_balance"] or 0) * rnd.uniform(0.9, 1.1), 2))
        pairs.append(f"{src['account_id']}/{dst['account_id']}")
    record("A15", "accounts", "client_id, client_account_number",
           "The same creditor account placed twice under two different account_ids, with slightly "
           "different placement dates and balances.", pairs,
           "Group by client_id + client_account_number having count > 1. Sample values are id pairs.")

    # A16 -- assignment pointing at staff who cannot work the account.
    targets = sample(120, lambda a: a["account_status"] not in CLOSED_SET)
    for a in targets:
        a["assigned_user_id"] = str(pick(terminated))
    record("A16a", "accounts", "assigned_user_id",
           "Open accounts assigned to users whose user_status is TERMINATED.",
           [a["account_id"] for a in targets],
           "Join accounts to users on assigned_user_id and filter on user_status.")
    targets = sample(9)
    for a in targets:
        a["assigned_user_id"] = str(rnd.choice([7777, 8888, 9999, 0]))
    record("A16b", "accounts", "assigned_user_id",
           "assigned_user_id values that do not exist in users.csv.",
           [a["account_id"] for a in targets])

    # A17 -- orphaned client references.
    targets = sample(4)
    for a in targets:
        a["client_id"] = pick([199, 250, 888])
    record("A17", "accounts", "client_id", "client_id values with no matching row in clients.csv.",
           [a["account_id"] for a in targets])

    # A18 -- inconsistent name hygiene.
    targets = sample(140)
    for a in targets:
        mode = weighted([("upper", 0.35), ("pad", 0.25), ("suffix_in_last", 0.15),
                         ("lower", 0.15), ("punct", 0.10)])
        if mode == "upper":
            a["first_name"] = a["first_name"].upper()
            a["last_name"] = a["last_name"].upper()
        elif mode == "pad":
            a["first_name"] = f" {a['first_name']} "
            a["last_name"] = f"{a['last_name']}  "
        elif mode == "suffix_in_last":
            a["last_name"] = f"{a['last_name']} {pick(SUFFIXES)}"
        elif mode == "lower":
            a["first_name"] = a["first_name"].lower()
            a["last_name"] = a["last_name"].lower()
        else:
            a["last_name"] = f"{a['last_name']}."
    record("A18", "accounts", "first_name, last_name",
           "Name hygiene problems: mixed casing, leading and trailing whitespace, suffixes stuffed "
           "into last_name, stray punctuation.", [a["account_id"] for a in targets])

    # A19 -- date sequences that cannot have happened.
    targets = sample(15)
    for a in targets:
        a["charge_off_date"] = iso(a["_placement"] + timedelta(days=rnd.randint(10, 200)))
    record("A19a", "accounts", "charge_off_date, placement_date",
           "charge_off_date falls after placement_date; an account cannot be placed before it charges off.",
           [a["account_id"] for a in targets])
    targets = sample(10)
    for a in targets:
        a["date_of_first_delinquency"] = iso(date.fromisoformat(a["charge_off_date"]) + timedelta(days=rnd.randint(5, 90)))
    record("A19b", "accounts", "date_of_first_delinquency, charge_off_date",
           "date_of_first_delinquency falls after charge_off_date, which distorts credit reporting and statute math.",
           [a["account_id"] for a in targets])

    # A20 -- payment summary fields that disagree with payments.csv.
    targets = sample(30, lambda a: not a["_payments"])
    for a in targets:
        a["last_payment_date"] = iso(rand_date(a["_placement"], TODAY))
        a["last_payment_amount"] = money(round(rnd.uniform(25, 400), 2))
    record("A20a", "accounts", "last_payment_date, last_payment_amount",
           "Accounts showing a last payment when payments.csv holds no payment for them at all.",
           [a["account_id"] for a in targets],
           "The single most useful cross-file reconciliation in the set.")
    targets = sample(50, lambda a: a["_payments"] and float(a["total_paid"]) > 0)
    for a in targets:
        a["total_paid"] = money(round(float(a["total_paid"]) * rnd.choice([0.5, 0.75, 1.3, 1.6]), 2))
    record("A20b", "accounts", "total_paid",
           "accounts.total_paid does not equal the sum of POSTED payments in payments.csv.",
           [a["account_id"] for a in targets])

    # A21 -- currency formatting leaking into numeric columns.
    targets = sample(12)
    for a in targets:
        for col in ("current_balance", "placement_balance"):
            v = float(a[col].replace("$", "").replace(",", "") or 0)
            a[col] = f"${v:,.2f}"
    record("A21", "accounts", "current_balance, placement_balance",
           "A handful of balance cells carry a dollar sign and thousands separators, so the column "
           "loads as text instead of a number.", [a["account_id"] for a in targets],
           "Whoever loads the file naively will get a type error or silent string sort here.")

    # A22 -- status_date earlier than placement_date.
    targets = sample(9)
    for a in targets:
        a["status_date"] = iso(a["_placement"] - timedelta(days=rnd.randint(5, 60)))
    record("A22", "accounts", "status_date, placement_date",
           "status_date precedes placement_date.", [a["account_id"] for a in targets])

    # A23 -- closed accounts still queued for work.
    targets = sample(40, lambda a: a["account_status"] in CLOSED_SET)
    for a in targets:
        a["next_action_date"] = iso(TODAY + timedelta(days=rnd.randint(1, 40)))
    record("A23", "accounts", "next_action_date, account_status",
           "Closed accounts still carrying a future next_action_date, so they stay in collector queues.",
           [a["account_id"] for a in targets])

    # A24 -- inconsistent representations of "no value".
    targets = sample(70)
    for a in targets:
        col = pick(["employer_name", "address_line2", "middle_initial", "phone_work", "email"])
        a[col] = pick(["NULL", "N/A", "n/a", "-", "UNKNOWN", "none"])
    record("A24", "accounts", "employer_name, address_line2, middle_initial, phone_work, email",
           "Empty values written five different ways: blank, NULL, N/A, n/a, -, UNKNOWN, none.",
           [a["account_id"] for a in targets],
           "Anything counting nulls will undercount unless these are normalized first.")

    # A25 -- state codes that are not states.
    targets = sample(6, lambda a: a["state"])
    for a in targets:
        a["state"] = pick(["XX", "ZZ", "US", "N/A", "  ", "Ca"])
    record("A25", "accounts", "state", "Invalid or non-standard state codes.",
           [a["account_id"] for a in targets])

    # A28 -- settlements booked against clients whose contract forbids settling.
    targets = sample(15, lambda a: a["_client"]["allows_settlement"] == "N"
                     and a["account_status"] == "PAID_IN_FULL")
    for a in targets:
        a["account_status"] = "SETTLED_IN_FULL"
        a["close_reason"] = CLOSE_REASONS["SETTLED_IN_FULL"]
        a["status_class"] = STATUS_CLASS[a["account_status"]]
    record("A28", "accounts", "account_status, client_id",
           "Accounts closed as SETTLED_IN_FULL under clients whose contract sets allows_settlement = N.",
           [a["account_id"] for a in targets],
           "Join accounts to clients and check account_status against allows_settlement.")

    # A29 -- the status_class rollup was never refreshed when the status moved on.
    stale_closed = sample(22, lambda a: a["account_status"] in CLOSED_SET)
    for a in stale_closed:
        a["status_class"] = pick(["OPEN", "OPEN", "PTP"])
    stale_open = sample(8, lambda a: a["account_status"] not in CLOSED_SET)
    for a in stale_open:
        a["status_class"] = "CLOSED"
    record("A29", "accounts", "status_class, account_status",
           "status_class disagrees with account_status. Most are closed accounts still classed as "
           "OPEN or PTP, so they inflate open inventory and stay in work queues; a few are open "
           "accounts classed CLOSED, so they disappear from reporting.",
           [a["account_id"] for a in stale_closed + stale_open],
           "status_class is a denormalized rollup of account_status. Rebuild it from the status and "
           "compare, rather than trusting the stored value.")

    # A30 -- the consumer paid the creditor directly after the account was placed.
    targets = sample(40, lambda a: a["client_last_payment_date"] and a["account_status"] not in CLOSED_SET)
    for a in targets:
        after = rand_date(a["_placement"] + timedelta(days=10), TODAY)
        a["client_last_payment_date"] = iso(after)
        a["client_last_payment_amount"] = money(round(float(a["placement_balance"].replace("$", "").replace(",", ""))
                                                      * rnd.uniform(0.05, 0.4), 2))
    record("A30", "accounts", "client_last_payment_date, placement_date",
           "The last payment to the original creditor is dated after placement, so the consumer paid "
           "the client directly while the agency kept collecting. The agency balance was never reduced.",
           [a["account_id"] for a in targets],
           "Real and expensive: it causes double collection and client disputes. Compare "
           "client_last_payment_date against placement_date.")

    # A26 -- consumers with several accounts, which is legitimate and worth spotting.
    anchors = sample(30, lambda a: a["ssn"] and "-" in a["ssn"])
    linked = []
    for anchor in anchors:
        others = sample(rnd.randint(2, 4), lambda a, anc=anchor: a["account_id"] != anc["account_id"])
        for o in others:
            for field in ("first_name", "last_name", "ssn", "date_of_birth", "address_line1",
                          "city", "state", "zip_code", "phone_cell"):
                o[field] = anchor[field]
            linked.append(o["account_id"])
    record("A26", "accounts", "ssn, last_name",
           "Not a defect: roughly 30 consumers hold multiple accounts across different clients. "
           "The set rewards recognizing this before deduplicating.",
           [a["account_id"] for a in anchors],
           "Distinguish these from the true duplicates in A15.")

    # A15 and A26 copy a whole identity from one row to another, which can hand a
    # complete address back to a row A1 had blanked. Re-derive A1 from the finished data.
    incomplete = [a["account_id"] for a in accounts
                  if not (a["address_line1"].strip() and a["city"].strip()
                          and a["state"].strip() and a["zip_code"].strip())]
    for issue in ISSUES:
        if issue["code"] == "A1":
            issue["count"] = len(incomplete)
            issue["samples"] = incomplete[:6]


def corrupt_payments(payments, accounts):
    valid_ids = {a["account_id"] for a in accounts}
    by_id = {a["account_id"]: a for a in accounts}

    def sample(k, predicate=None):
        pool = [p for p in payments if predicate is None or predicate(p)]
        rnd.shuffle(pool)
        return pool[:k]

    targets = sample(12)
    for p in targets:
        p["account_id"] = rnd.choice([999999, 500000, 888888])
    record("P1", "payments", "account_id", "Payments referencing account_ids that are not in accounts.csv.",
           [p["payment_id"] for p in targets])

    targets = sample(25, lambda p: by_id.get(p["account_id"], {}).get("_closed_date"))
    for p in targets:
        acct = by_id[p["account_id"]]
        newd = acct["_closed_date"] + timedelta(days=rnd.randint(10, 120))
        if newd > TODAY:
            newd = TODAY
        p["payment_date"] = iso(newd)
        p["posted_date"] = iso(newd + timedelta(days=1))
    record("P2", "payments", "payment_date",
           "Payments dated after the account was closed, including payments taken on bankruptcy and deceased accounts.",
           [p["payment_id"] for p in targets],
           "Join to accounts.closed_date. Some of these are compliance problems, not just data problems.")

    targets = sample(10, lambda p: p["payment_status"] == "POSTED")
    for p in targets:
        p["payment_amount"] = money(rnd.choice([0.0, 0.0, -25.0, -50.0]))
    record("P3", "payments", "payment_amount", "Posted payments with a zero or negative amount.",
           [p["payment_id"] for p in targets])

    targets = sample(15, lambda p: p["payment_status"] == "POSTED")
    dupe_ids = []
    for p in targets:
        clone = dict(p)
        clone["payment_id"] = 9800000 + len(dupe_ids)
        clone["transaction_reference"] = p["transaction_reference"]
        payments.append(clone)
        dupe_ids.append(f"{p['payment_id']}/{clone['payment_id']}")
    record("P4", "payments", "payment_id, transaction_reference",
           "Duplicate payment rows: identical account, date, amount and transaction reference under two payment_ids.",
           dupe_ids, "Sample values are id pairs. Also inflates total collections if counted naively.")

    targets = sample(6)
    for p in targets:
        d = TODAY + timedelta(days=rnd.randint(5, 90))
        p["payment_date"] = iso(d)
        p["posted_date"] = iso(d)
    record("P5", "payments", "payment_date", "Payment dates in the future.",
           [p["payment_id"] for p in targets])

    targets = sample(20)
    for p in targets:
        p["received_by_user_id"] = pick(["", "0", "9999", "UNKNOWN"])
    record("P6", "payments", "received_by_user_id", "Missing or invalid receiving user on the payment.",
           [p["payment_id"] for p in targets])

    targets = sample(5, lambda p: p["account_id"] in valid_ids)
    for p in targets:
        acct = by_id[p["account_id"]]
        d = acct["_placement"] - timedelta(days=rnd.randint(5, 60))
        p["payment_date"] = iso(d)
        p["posted_date"] = iso(d)
    record("P7", "payments", "payment_date, posted_date",
           "Payments posted before the account was ever placed with the agency.",
           [p["payment_id"] for p in targets])

    targets = sample(18, lambda p: p["payment_status"] == "POSTED" and p["payment_method"] == "CHECK")
    for p in targets:
        p["payment_method"] = pick(["check", "Check", "CHK", "ACH_DEBIT", "ach"])
    record("P8", "payments", "payment_method",
           "Payment method spelled several different ways for the same method.",
           [p["payment_id"] for p in targets],
           "Grouping by payment_method without normalizing splits the same method across buckets.")


def corrupt_arrangements(arrangements, accounts):
    by_id = {a["account_id"]: a for a in accounts}

    def sample(k, predicate=None):
        pool = [r for r in arrangements if predicate is None or predicate(r)]
        rnd.shuffle(pool)
        return pool[:k]

    targets = sample(60, lambda r: r["arrangement_status"] == "ACTIVE")
    for r in targets:
        r["next_payment_date"] = iso(TODAY - timedelta(days=rnd.randint(75, 400)))
    record("R1", "payment_arrangements", "arrangement_status, next_payment_date",
           "Arrangements still marked ACTIVE whose next payment was due months ago; they are broken "
           "but nothing reflects it.", [r["arrangement_id"] for r in targets],
           "These accounts are also still counted in 'accounts on a plan' reporting.")

    targets = sample(18, lambda r: by_id.get(r["account_id"], {}).get("_closed_date")
                     and r["arrangement_status"] in ("BROKEN", "CANCELLED", "COMPLETED"))
    for r in targets:
        r["arrangement_status"] = "ACTIVE"
        r["next_payment_date"] = iso(TODAY + timedelta(days=rnd.randint(3, 40)))
        r["broken_date"] = ""
        r["broken_reason"] = ""
    record("R2", "payment_arrangements", "arrangement_status",
           "Active arrangements, with a future payment still scheduled, sitting on accounts that are "
           "already closed. Several of these accounts are closed as bankruptcy or deceased.",
           [r["arrangement_id"] for r in targets],
           "Join arrangements to accounts.closed_date.")

    targets = sample(30)
    for r in targets:
        r["installment_amount"] = money(round(float(r["installment_amount"]) * rnd.uniform(1.3, 2.2), 2))
    record("R3", "payment_arrangements", "installment_amount, number_of_installments, total_amount",
           "installment_amount times number_of_installments does not reconcile to total_amount.",
           [r["arrangement_id"] for r in targets])

    targets = sample(12, lambda r: r["payments_made"] == "0")
    for r in targets:
        r["payments_made"] = str(rnd.randint(2, 6))
        r["amount_paid_to_date"] = money(round(float(r["installment_amount"]) * int(r["payments_made"]), 2))
    record("R4", "payment_arrangements", "payments_made, amount_paid_to_date",
           "Arrangements claiming payments were made when payments.csv has none for that arrangement.",
           [r["arrangement_id"] for r in targets])

    targets = sample(10, lambda r: r["arrangement_status"] == "ACTIVE")
    clones = []
    for r in targets:
        clone = dict(r)
        clone["arrangement_id"] = 790000 + len(clones)
        clone["created_date"] = iso(date.fromisoformat(r["created_date"]) + timedelta(days=rnd.randint(5, 60)))
        clones.append(clone)
    arrangements.extend(clones)
    record("R5", "payment_arrangements", "account_id, arrangement_status",
           "Two simultaneously ACTIVE arrangements on the same account.",
           [f"{r['account_id']}" for r in clones],
           "Sample values are account_ids. Group by account_id where status = ACTIVE.")

    targets = sample(8, lambda r: r["arrangement_status"] == "ACTIVE" and not r["broken_date"])
    for r in targets:
        r["broken_date"] = iso(TODAY - timedelta(days=rnd.randint(20, 200)))
        r["broken_reason"] = "MISSED SCHEDULED PAYMENT"
    record("R6", "payment_arrangements", "arrangement_status, broken_date",
           "broken_date and broken_reason populated while arrangement_status is still ACTIVE.",
           [r["arrangement_id"] for r in targets])


# --------------------------------------------------------------------------
# Output
# --------------------------------------------------------------------------

def write_csv(name, columns, rows):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
        w.writerow(columns)
        for r in rows:
            w.writerow([r.get(c, "") for c in columns])
    return path


def parse_args():
    ap = argparse.ArgumentParser(
        description="Generate a synthetic collections data set.",
        epilog=("Examples:\n"
                "  python generate.py\n"
                "  python generate.py --accounts 500 --out sample\n"
                '  python generate.py --seed "Data Set A" --out data_a --key ANSWER_KEY_A.md\n'
                '  python generate.py --seed "Data Set B" --out data_b --key ANSWER_KEY_B.md\n'
                "\n"
                "The last two are the matched pair ab_check.py expects: same model,\n"
                "different noise, so a scorecard fitted on A can be tested on B."),
        formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", default=SEED, metavar="SEED",
                    help='Any text or integer. The same seed and the same version of this '
                         'script always produce the same files, so a seed names a data set '
                         'rather than randomizing it. Default: "%(default)s"')
    ap.add_argument("--out", default="data", metavar="DIR",
                    help="Directory for the six CSV files, created if missing. Relative to "
                         "this script unless absolute. Default: %(default)s")
    ap.add_argument("--key", default="ANSWER_KEY.md", metavar="PATH",
                    help="Where to write the answer key. Relative to this script unless "
                         "absolute. Default: %(default)s")
    ap.add_argument("--accounts", type=int, default=ACCOUNT_COUNT, metavar="N",
                    help="How many accounts to generate. Every other file scales with it. "
                         "Default: %(default)s")
    return ap.parse_args()


def main():
    global OUT_DIR, ACCOUNT_COUNT, KEY_PATH
    args = parse_args()
    # "12345" on the command line should mean the integer, not the text.
    seed = args.seed
    if isinstance(seed, str) and seed.lstrip("-").isdigit():
        seed = int(seed)
    rnd.seed(seed)
    OUT_DIR = args.out if os.path.isabs(args.out) else os.path.join(BASE_DIR, args.out)
    KEY_PATH = args.key if os.path.isabs(args.key) else os.path.join(BASE_DIR, args.key)
    ACCOUNT_COUNT = args.accounts
    ISSUES.clear()
    os.makedirs(OUT_DIR, exist_ok=True)
    print(f'seed "{seed}" -> {os.path.relpath(OUT_DIR, BASE_DIR)}/')

    clients = build_clients()
    users = build_users()
    accounts = build_accounts(clients, users)
    payments, arrangements = build_money(accounts, users)

    # Notes are generated before the account corruption pass so that note text
    # reflects the clean values, then the flags get broken underneath them.
    notes_path = os.path.join(OUT_DIR, "notes.csv")
    with open(notes_path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, quoting=csv.QUOTE_MINIMAL)
        w.writerow(NOTE_COLUMNS)
        _, note_count = build_notes(accounts, users, w)

    corrupt_accounts(accounts, users, clients)
    corrupt_payments(payments, accounts)
    corrupt_arrangements(arrangements, accounts)

    write_csv("clients.csv", CLIENT_COLUMNS, clients)
    write_csv("users.csv", USER_COLUMNS, users)
    write_csv("accounts.csv", ACCOUNT_COLUMNS, accounts)
    write_csv("payments.csv", PAYMENT_COLUMNS, payments)
    write_csv("payment_arrangements.csv", ARRANGEMENT_COLUMNS, arrangements)

    write_answer_key(accounts, payments, arrangements, note_count, clients, users)

    # Console summary
    closed = sum(1 for a in accounts if a["account_status"] in CLOSED_SET)
    print(f"clients                {len(clients):>8,}")
    print(f"users                  {len(users):>8,}")
    print(f"accounts               {len(accounts):>8,}   ({closed:,} closed = {closed/len(accounts):.1%})")
    print(f"payments               {len(payments):>8,}")
    print(f"payment_arrangements   {len(arrangements):>8,}")
    print(f"notes                  {note_count:>8,}   ({note_count/len(accounts):.1f} per account)")
    print(f"planted defects        {len(ISSUES):>8,}")


def write_answer_key(accounts, payments, arrangements, note_count, clients, users):
    closed = sum(1 for a in accounts if a["account_status"] in CLOSED_SET)
    lines = []
    lines.append("# Answer key")
    lines.append("")
    lines.append("Every defect planted in this data set, plus the true coefficients of the "
                 "propensity model. Written by `generate.py` on each run, so it always matches "
                 "the files sitting next to it.")
    lines.append("")
    lines.append("Hold this back if you want someone to find the issues on their own.")
    lines.append("")
    lines.append("## Volumes")
    lines.append("")
    lines.append("| File | Rows |")
    lines.append("| --- | ---: |")
    lines.append(f"| clients.csv | {len(clients):,} |")
    lines.append(f"| users.csv | {len(users):,} |")
    lines.append(f"| accounts.csv | {len(accounts):,} ({closed:,} closed, {closed/len(accounts):.1%}) |")
    lines.append(f"| payments.csv | {len(payments):,} |")
    lines.append(f"| payment_arrangements.csv | {len(arrangements):,} |")
    lines.append(f"| notes.csv | {note_count:,} |")
    lines.append("")
    lines.append("## Identifier safety")
    lines.append("")
    lines.append("Every phone number in the set uses the 555 exchange and every SSN breaks an SSA "
                 "issuance rule (area 000 / 666 / 900-999, group 00, or serial 0000), so none of them "
                 "can reach or identify a real "
                 "person. Defect A11 is junk typed into the SSN field, not an invalid SSN, because "
                 "every SSN here is already unissuable.")
    lines.append("")
    liq = sum(1 for a in accounts if float(a["total_paid"].replace("$", "").replace(",", "") or 0) > 0)
    lines.append("## The propensity model")
    lines.append("")
    lines.append("Liquidation in this data is not random. Every account carries a latent propensity "
                 "drawn from the fixed logistic model below, and that score decides whether it pays, "
                 "how much and how often, what status it lands in, and how its right party "
                 "contacts go.")
    lines.append("")
    lines.append("The coefficients are constants in `generate.py`, not seeded, so any two data sets "
                 "share this model and differ only in noise. A scorecard fitted on one should hold "
                 "its shape on the other. Run `python ab_check.py` to see that measured.")
    lines.append("")
    lines.append("Log-odds that an account ever pays anything:")
    lines.append("")
    lines.append("| Term | Coefficient |")
    lines.append("| --- | ---: |")
    lines.append(f"| Intercept | {PROPENSITY_INTERCEPT:+.2f} |")
    lines.append(f"| Debt age at placement, per year from charge-off to placement | {W_DEBT_AGE:+.2f} |")
    lines.append(f"| Placement balance, per 10x above a $250 base | {W_LOG_BALANCE:+.2f} |")
    lines.append(f"| Consumer paid the original creditor at some point | {W_CLIENT_PAID:+.2f} |")
    lines.append(f"| ... and how recently, decaying to zero over 24 months | {W_CLIENT_PAID_RECENCY:+.2f} |")
    lines.append(f"| Cell phone on file | {W_HAS_CELL:+.2f} |")
    lines.append(f"| Home phone on file | {W_HAS_HOME:+.2f} |")
    lines.append(f"| No phone of any kind | {W_NO_PHONE:+.2f} |")
    lines.append(f"| Phone status VERIFIED | {W_PHONE_GOOD:+.2f} |")
    lines.append(f"| Phone status BAD, DISCONNECTED or WRONG_NUMBER | {W_PHONE_BAD:+.2f} |")
    lines.append(f"| Address status VERIFIED | {W_ADDRESS_GOOD:+.2f} |")
    lines.append(f"| Address status BAD | {W_ADDRESS_BAD:+.2f} |")
    lines.append(f"| No address provided | {W_NO_ADDRESS:+.2f} |")
    lines.append(f"| Client lift, scaled by | {W_CLIENT_LIFT:.2f} |")
    for prod, w in sorted(PRODUCT_PROPENSITY.items(), key=lambda kv: -kv[1]):
        lines.append(f"| Product type {prod} | {w:+.2f} |")
    lines.append(f"| Gaussian noise, standard deviation | {PROPENSITY_NOISE_SD:.2f} |")
    lines.append("")
    lines.append("Each client also carries its own lift, standing in for data quality at placement, "
                 "how hard the creditor worked the account first, and who their customers are. "
                 "Clients inside one product class deliberately differ, which is what makes client "
                 "and product type separate signals rather than the same one twice. A few clients "
                 "place more than one kind of paper so the two are not perfectly collinear.")
    lines.append("")
    lines.append("| Client | Product mix | Lift |")
    lines.append("| --- | --- | ---: |")
    for c in clients:
        mix = ", ".join(f"{p} {int(w * 100)}%" if w < 1 else p for p, w in c["_products"])
        lines.append(f"| {c['client_name']} ({c['client_id']}) | {mix} | {c['_lift']:+.2f} |")
    lines.append("")
    lines.append(f"That latent score is then multiplied by an exposure term, "
                 f"`1 - exp(-days_on_book / {LIQUIDATION_TIME_CONSTANT_DAYS})`, because an account "
                 f"placed last month has not had time to show what it is worth. Debt age and time on "
                 f"book are separate things here, and conflating them is the most common way to get "
                 f"this analysis wrong.")
    lines.append("")
    lines.append(f"In this data set {liq:,} accounts ({liq / len(accounts):.1%}) paid something.")
    lines.append("")
    lines.append("Two modeling exercises this supports:")
    lines.append("")
    lines.append("1. **Placement scoring.** Predict liquidation using only what was known at "
                 "placement: debt age, balance, client last payment, product type, contact data. "
                 "This is the model the table above describes.")
    lines.append("2. **In-treatment scoring.** Predict payment after day 90 using agency activity in "
                 "the first 90 days, such as whether a right party contact happened or a promise to "
                 "pay was logged. Those features are far stronger, and they are partly self "
                 "fulfilling, so they only make sense with a time split. Without one they leak.")
    lines.append("")
    lines.append("## Fields that are always reliable")
    lines.append("")
    lines.append("These are populated on every account row and are internally consistent, so they "
                 "are safe to anchor on: `account_id`, `client_account_number`, `placement_date`, "
                 "`account_status`, `status_date`, `original_balance`, `placement_balance`. Note that "
                 "`placement_balance` carries a dollar sign on twelve rows (defect A21); the value itself "
                 "is still correct.")
    lines.append("")
    lines.append("## Planted defects")
    lines.append("")
    def code_key(issue):
        code = issue["code"]
        digits = "".join(c for c in code if c.isdigit())
        return (code[0], int(digits or 0), code)

    by_table = {}
    for issue in ISSUES:
        by_table.setdefault(issue["table"], []).append(issue)
    for table in by_table:
        by_table[table].sort(key=code_key)
    for table in ["accounts", "payments", "payment_arrangements", "notes", "clients", "users"]:
        if table not in by_table:
            continue
        lines.append(f"### {table}")
        lines.append("")
        for issue in by_table[table]:
            samples = ", ".join(str(s) for s in issue["samples"])
            lines.append(f"**{issue['code']} - {issue['columns']}** ({issue['count']} rows)")
            lines.append("")
            lines.append(issue["description"])
            if issue["hint"]:
                lines.append("")
                lines.append(f"*{issue['hint']}*")
            lines.append("")
            lines.append(f"Sample ids: {samples}")
            lines.append("")
    lines.append("## What this data is good for")
    lines.append("")
    for item in [
        "Load it into your warehouse or application and see which columns the ingest chokes "
        "on. The embedded newlines, the dollar signs in numeric columns and the two date "
        "formats are all there on purpose.",
        "Profile every file and produce a data dictionary without being told the schema.",
        "Reconcile `accounts.total_paid` against the sum of POSTED payments and explain each break.",
        "Find every account where the notes contradict the compliance flags (A8, N4a, N4b).",
        "Build a collector performance report from notes and payments, then explain why the numbers "
        "are wrong until terminated users and duplicate payments are handled.",
        "Identify accounts that should never have been worked: bankruptcy, deceased, cease and desist.",
        "Measure liquidation rate by client and by placement year, and defend the denominator chosen.",
        "Count how many distinct consumers exist. The answer depends on how A12, A15 and A26 are treated.",
        "Rebuild status_class from account_status and find the rows where the stored rollup disagrees, then say what that does to an open inventory count.",
        "Find the FDCPA calling-window violations in the notes (N3).",
    ]:
        lines.append(f"- {item}")
    lines.append("")
    with open(KEY_PATH, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines))


if __name__ == "__main__":
    main()
