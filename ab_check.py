"""
Fit a liquidation scorecard on one data set and test it on another.

This is the proof that the injected propensity pattern is real and that it
transfers: train on A, score B, and compare AUC and decile lift. A pattern that
only exists in A is noise. One that holds on B is a pattern.

There are no third party dependencies. The logistic regression is plain gradient
descent on standardized features with a light L2 penalty, which is more than enough
for fifty features and ten thousand rows.

Individual client dummies carry small standardized coefficients because each client
covers only a few percent of the file. The client effect is real; look at liquidation
by client within a single product type to see it plainly.

Usage:
    python generate.py --seed "Data Set A" --out data_a --key ANSWER_KEY_A.md
    python generate.py --seed "Data Set B" --out data_b --key ANSWER_KEY_B.md
    python ab_check.py data_a data_b
"""

import csv
import math
import os
import sys
from collections import defaultdict
from datetime import date

TODAY = date(2026, 8, 20)

# Product types get one column each so the model has to learn them rather than
# being handed the generator's weights.
PRODUCTS = ["MEDICAL", "DENTAL", "CREDIT_CARD", "RETAIL_CARD", "PERSONAL_LOAN",
            "AUTO_DEFICIENCY", "UTILITY", "TELECOM", "RENTAL", "STUDENT_LOAN",
            "GYM_MEMBERSHIP", "VETERINARY", "SUBROGATION"]


def num(value):
    """Parse a money field, tolerating the dollar signs and commas in the data."""
    try:
        return float(str(value).replace("$", "").replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def parse_date(value):
    try:
        return date.fromisoformat(value.strip()[:10])
    except (ValueError, AttributeError):
        return None


def client_ids(directory):
    """Stable client id ordering, so A and B share the same dummy columns."""
    with open(os.path.join(directory, "clients.csv"), newline="", encoding="utf-8") as fh:
        return sorted(row["client_id"] for row in csv.DictReader(fh))


def load(directory, clients):
    """Build a feature matrix and the liquidation target for one data set."""
    def read(name):
        with open(os.path.join(directory, name), newline="", encoding="utf-8") as fh:
            return list(csv.DictReader(fh))

    accounts = read("accounts.csv")
    payments = read("payments.csv")

    # The target comes from payments.csv, not accounts.total_paid, because that
    # column is deliberately wrong on some rows. Only POSTED money counts.
    posted = defaultdict(float)
    for p in payments:
        if p["payment_status"] == "POSTED":
            amount = num(p["payment_amount"])
            if amount and amount > 0:
                posted[p["account_id"]] += amount

    rows, targets, meta = [], [], []
    for a in accounts:
        placement = parse_date(a["placement_date"])
        charge_off = parse_date(a["charge_off_date"])
        balance = num(a["placement_balance"])
        if not (placement and charge_off) or not balance or balance <= 0:
            continue

        debt_age_years = (placement - charge_off).days / 365.25
        days_on_book = (TODAY - placement).days
        client_paid = parse_date(a["client_last_payment_date"])
        # A client payment dated after placement is defect A30, not a placement
        # time feature, so it does not count as prior payment history.
        has_client_paid = 1.0 if (client_paid and client_paid <= placement) else 0.0
        recency = 0.0
        if has_client_paid:
            recency = max(0.0, 1.0 - (placement - client_paid).days / 730.0)

        features = [
            debt_age_years,
            math.log10(max(balance, 25.0) / 250.0),
            has_client_paid,
            recency,
            1.0 if a["phone_cell"].strip() else 0.0,
            1.0 if a["phone_home"].strip() else 0.0,
            1.0 if a["phone_status"] == "VERIFIED" else 0.0,
            1.0 if a["phone_status"] in ("BAD", "DISCONNECTED", "WRONG_NUMBER") else 0.0,
            1.0 if a["phone_status"] == "NONE" else 0.0,
            1.0 if a["address_status"] == "VERIFIED" else 0.0,
            1.0 if a["address_status"] == "BAD" else 0.0,
            1.0 if a["address_status"] == "NONE" else 0.0,
            # Exposure control: a new account has not had time to pay yet.
            1.0 - math.exp(-max(0, days_on_book) / 165.0),
        ]
        features += [1.0 if a["product_type"] == p else 0.0 for p in PRODUCTS]
        # Client identity matters on its own, separately from what the debt is for.
        features += [1.0 if a["client_id"] == c else 0.0 for c in clients]

        rows.append(features)
        targets.append(1 if posted.get(a["account_id"], 0.0) > 0 else 0)
        meta.append(a["account_id"])
    return rows, targets, meta


BASE_FEATURES = ["debt_age_years", "log10_balance", "has_client_payment",
                 "client_payment_recency", "has_cell", "has_home",
                 "phone_verified", "phone_bad", "phone_none",
                 "address_verified", "address_bad", "address_none", "exposure"]


def feature_names(clients):
    return (BASE_FEATURES + [f"product_{p}" for p in PRODUCTS]
            + [f"client_{c}" for c in clients])


def standardize(rows):
    n_features = len(rows[0])
    means, sds = [], []
    for j in range(n_features):
        column = [r[j] for r in rows]
        mean = sum(column) / len(column)
        var = sum((v - mean) ** 2 for v in column) / len(column)
        means.append(mean)
        sds.append(math.sqrt(var) or 1.0)
    return means, sds


def apply_scaling(rows, means, sds):
    return [[(r[j] - means[j]) / sds[j] for j in range(len(r))] for r in rows]


def fit(rows, targets, iterations=300, lr=1.2, l2=0.02):
    """
    Batch gradient descent on the log loss, with a light L2 penalty.

    The penalty matters here: there are twenty two client dummies, and the
    smaller clients carry only a few hundred accounts each, so an unpenalized
    fit spends parameters on noise and the holdout gap widens.
    """
    n, k = len(rows), len(rows[0])
    weights = [0.0] * k
    bias = 0.0
    for _ in range(iterations):
        grad_w = [0.0] * k
        grad_b = 0.0
        for xi, yi in zip(rows, targets):
            z = bias + sum(w * x for w, x in zip(weights, xi))
            pred = 1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, z))))
            err = pred - yi
            grad_b += err
            for j in range(k):
                grad_w[j] += err * xi[j]
        bias -= lr * grad_b / n
        for j in range(k):
            weights[j] -= lr * (grad_w[j] / n + l2 * weights[j])
    return weights, bias


def predict(rows, weights, bias):
    out = []
    for xi in rows:
        z = bias + sum(w * x for w, x in zip(weights, xi))
        out.append(1.0 / (1.0 + math.exp(-max(-35.0, min(35.0, z)))))
    return out


def auc(scores, targets):
    """Rank based AUC, with ties averaged."""
    paired = sorted(zip(scores, targets))
    ranks = [0.0] * len(paired)
    i = 0
    while i < len(paired):
        j = i
        while j + 1 < len(paired) and paired[j + 1][0] == paired[i][0]:
            j += 1
        average_rank = (i + j) / 2.0 + 1.0
        for k in range(i, j + 1):
            ranks[k] = average_rank
        i = j + 1
    positives = sum(t for _, t in paired)
    negatives = len(paired) - positives
    if not positives or not negatives:
        return float("nan")
    rank_sum = sum(r for r, (_, t) in zip(ranks, paired) if t == 1)
    return (rank_sum - positives * (positives + 1) / 2.0) / (positives * negatives)


def decile_table(scores, targets):
    order = sorted(range(len(scores)), key=lambda i: -scores[i])
    size = len(order) // 10
    base = sum(targets) / len(targets)
    out = []
    for d in range(10):
        chunk = order[d * size:(d + 1) * size] if d < 9 else order[d * size:]
        rate = sum(targets[i] for i in chunk) / len(chunk)
        out.append((rate, rate / base if base else 0.0))
    return out


def main():
    dir_a = sys.argv[1] if len(sys.argv) > 1 else "data_a"
    dir_b = sys.argv[2] if len(sys.argv) > 2 else "data_b"
    base = os.path.dirname(os.path.abspath(__file__))
    dir_a = dir_a if os.path.isabs(dir_a) else os.path.join(base, dir_a)
    dir_b = dir_b if os.path.isabs(dir_b) else os.path.join(base, dir_b)

    for d in (dir_a, dir_b):
        if not os.path.isdir(d):
            sys.exit(f"Missing directory {d}. Generate the pair first; see the header of this file.")

    clients = client_ids(dir_a)
    names = feature_names(clients)
    rows_a, y_a, _ = load(dir_a, clients)
    rows_b, y_b, _ = load(dir_b, clients)
    print(f"A: {os.path.basename(dir_a)}  {len(rows_a):,} accounts, {sum(y_a) / len(y_a):.1%} liquidated")
    print(f"B: {os.path.basename(dir_b)}  {len(rows_b):,} accounts, {sum(y_b) / len(y_b):.1%} liquidated")
    print()

    means, sds = standardize(rows_a)
    scaled_a = apply_scaling(rows_a, means, sds)
    scaled_b = apply_scaling(rows_b, means, sds)      # B uses A's scaling, as a holdout must

    weights, bias = fit(scaled_a, y_a)
    pred_a = predict(scaled_a, weights, bias)
    pred_b = predict(scaled_b, weights, bias)

    auc_a, auc_b = auc(pred_a, y_a), auc(pred_b, y_b)
    print("Model fitted on A, applied unchanged to B")
    print(f"  AUC on A (in sample)     {auc_a:.4f}")
    print(f"  AUC on B (never seen)    {auc_b:.4f}")
    print(f"  difference               {abs(auc_a - auc_b):.4f}")
    print()

    # Refit on B to compare what each data set says the drivers are.
    means_b, sds_b = standardize(rows_b)
    weights_b, _ = fit(apply_scaling(rows_b, means_b, sds_b), y_b)
    print("Standardized coefficients, fitted independently on each data set")
    print(f"({len(names)} features including product and client dummies; "
          f"terms under 0.02 on both sides are omitted)")
    print(f"  {'feature':26} {'A':>8} {'B':>8} {'diff':>8}")
    order = sorted(range(len(weights)), key=lambda j: -abs(weights[j]))
    for j in order:
        if abs(weights[j]) < 0.02 and abs(weights_b[j]) < 0.02:
            continue
        print(f"  {names[j]:26} {weights[j]:+8.3f} {weights_b[j]:+8.3f} "
              f"{abs(weights[j] - weights_b[j]):8.3f}")
    print()

    print("Decile lift, model scored on each data set")
    print(f"  {'decile':8} {'A rate':>8} {'A lift':>8} {'B rate':>8} {'B lift':>8}")
    for i, (a_row, b_row) in enumerate(zip(decile_table(pred_a, y_a), decile_table(pred_b, y_b)), start=1):
        print(f"  {i:<8} {a_row[0]:>7.1%} {a_row[1]:>8.2f} {b_row[0]:>7.1%} {b_row[1]:>8.2f}")


if __name__ == "__main__":
    main()
