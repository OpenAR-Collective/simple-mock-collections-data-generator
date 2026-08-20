# Simple Mock Collections Data Generator

A seeded Python script that builds a synthetic "database" for a fictional third party
debt collection agency, Acme Receivables Management, as six CSV files. It exists so
that participants in a hands on session can point an AI tool at a realistic operational
data set and work with it directly, without anyone having to expose real consumer data.

The data looks like a system that has been running for five years, which means it also
has the flaws of one. Sixty two classes of data quality defect are planted on purpose,
catalogued automatically as they are applied, and documented in a facilitator answer
key. Finding them is the exercise.

Everything is generated. The names, addresses, Social Security numbers, phone numbers,
email addresses, account numbers and clients are invented, and no row describes a real
person or a real debt.

## Quick start

You need Python 3.8 or newer. There are no third party dependencies; the script uses
only the standard library, so there is nothing to install and no virtual environment to
set up.

```bash
git clone https://github.com/OpenAR-Collective/simple-mock-collections-data-generator.git
```

```bash
cd simple-mock-collections-data-generator
```

```bash
python generate.py
```

On Windows, use `py generate.py` if `python` is not on your PATH.

That writes the six CSV files into a `data/` directory next to the script, along with
`ANSWER_KEY.md` in the repository root, and prints a summary:

```
clients                      16
users                        49
accounts                 10,000   (3,433 closed = 34.3%)
payments                 16,002
payment_arrangements      2,539
notes                   199,966   (20.0 per account)
planted defects              62
```

The whole run takes a few seconds and produces about 41 MB. To confirm the output is
sound, run the checks:

```bash
python validate.py
```

The generated files are not committed to this repository; `data/` is in `.gitignore`.
The generator is seeded, so any two people who run it get byte identical files.

### Tuning what you get

The constants at the top of `generate.py` control the shape of the data set:

| Constant | Default | Effect |
| --- | --- | --- |
| `SEED` | `20260820` | Change it for a completely different but equally valid data set |
| `ACCOUNT_COUNT` | `10_000` | Number of accounts, which drives every other file |
| `TODAY` | `2026-08-20` | The "now" every date in the set is relative to |
| `HISTORY_START` | `TODAY` minus 1,826 days | How far back placements go, five years by default |
| `NOTE_ACTIVITY_MEAN` | `16` | Collector activity notes per account, before system notes are added |

Volumes scale roughly linearly, so `ACCOUNT_COUNT = 500` gives a set small enough to
open in a spreadsheet.

## Why this is safe to hand out

The identifiers are not merely made up, they are impossible on purpose:

- **Every phone number uses the 555 exchange**, which carries no subscriber lines.
  A third of them fall in 555-0100 through 555-0199, the block reserved for fictional
  use, and 555-1212 is excluded because directory assistance is a live number. None of
  these can be dialed and reach a person.
- **Every Social Security number breaks an SSA issuance rule.** The SSA has never
  issued a number with an area of 000, 666 or 900-999, with a group of 00, or with a
  serial of 0000, and it will not issue any of those under the randomization scheme it
  has used since 2011. Every value here violates at least one of those rules, so none of
  them can belong to a person. The 900-999 numbers additionally avoid the group ranges
  the IRS uses for ITINs, so they cannot collide with a real taxpayer identifier either.

The handful of deliberately broken phone numbers in the data use area codes of 000,
111 and 999, which are unassignable, so they are unreachable as well.

## What the generator produces

Everything below lands in `data/`, which is not tracked in this repository. Run
`python generate.py` to create it.

| File | Rows | Size | What it holds |
| --- | ---: | ---: | --- |
| `data/accounts.csv` | 10,000 | 4.1 MB | One row per placed account, with the consumer's details on the same row |
| `data/notes.csv` | 199,966 | 35 MB | Collection activity notes, roughly 20 per account |
| `data/payments.csv` | 16,002 | 2.4 MB | Payment transactions, including returns and reversals |
| `data/payment_arrangements.csv` | 2,539 | 418 KB | Installment plans and settlement agreements |
| `data/clients.csv` | 16 | 3 KB | The creditors that place accounts with the agency |
| `data/users.csv` | 49 | 6 KB | Agency staff, from collectors to compliance |

All files are UTF-8, comma delimited, with a header row and RFC 4180 quoting. Note
that `notes.csv` contains free text with embedded commas, quotes and line breaks, so
it has to be read with a real CSV parser rather than split on newlines.

## How the files relate

```
clients.client_id ──< accounts.client_id
users.user_id     ──< accounts.assigned_user_id
                  ──< notes.user_id
                  ──< payments.received_by_user_id
                  ──< payment_arrangements.created_by_user_id

accounts.account_id ──< notes.account_id
                    ──< payments.account_id
                    ──< payment_arrangements.account_id

payment_arrangements.arrangement_id ──< payments.arrangement_id
```

The accounts table is deliberately flattened. A normalized system would keep consumers
and accounts in separate tables, since one consumer can hold several accounts, but here
the consumer's identity, address, phone numbers and demographics all sit on the account
row. Some consumers do appear on more than one account.

## Business background

Acme is a third party agency, which means it does not own these debts. Creditors
(the clients) place accounts with the agency to collect on their behalf, and the agency
earns a percentage of what it collects, called the contingency rate. Accounts flow in
continuously and are eventually closed, either because they were collected or because
they were returned to the client.

Terms that show up in the data:

- **Placement.** The date the creditor handed the account to the agency. This starts
  the clock on everything else.
- **Charge off.** The date the creditor wrote the debt off its own books, always before
  placement.
- **Date of first delinquency.** The date the consumer first fell behind and never
  caught up. It drives both credit reporting and the statute of limitations.
- **PIF and SIF.** Paid in full, and settled in full for less than the full balance.
- **PTP.** A promise to pay on a specific date for a specific amount.
- **NSF.** A payment returned by the bank for insufficient funds.
- **RPC.** Right party contact, meaning the agency actually reached the consumer rather
  than a voicemail box or a relative.
- **Cease and desist.** A consumer instruction to stop contacting them, which the agency
  is legally required to honor.
- **Calling window.** Under the FDCPA, collectors may only call between 8:00am and
  9:00pm in the consumer's local time.

## Data dictionary

### accounts.csv

One row per account. About a third of the file is closed.

`account_status` is the detailed status. `status_class` is a rollup of it, one class per
account, and it is what most reporting groups by:

| `status_class` | What it means | `account_status` values |
| --- | --- | --- |
| `OPEN` | Normal collectible inventory | `NEW`, `ACTIVE`, `SKIP_TRACE`, `SKIP_NO_HIT`, `CLIENT_HOLD`, `PENDING_CLIENT_REVIEW` |
| `PTP` | The consumer has a live commitment to pay | `PROMISE_TO_PAY`, `PAYMENT_PLAN`, `PAYMENT_PLAN_AT_RISK` |
| `SENSITIVE` | Still open, but standard collection activity has to stop until it is resolved | `DISPUTED`, `LEGAL`, `MILITARY_SCRA`, `HARDSHIP_REVIEW` |
| `CLOSED` | Finished, whatever the reason | `PAID_IN_FULL`, `SETTLED_IN_FULL`, `RETURNED`, `RECALLED`, `BANKRUPTCY`, `DECEASED`, `UNCOLLECTIBLE`, `STATUTE_EXPIRED` |

Bankruptcy and deceased accounts are classed `CLOSED` because they are closed. The fact
that they also demand careful handling is carried by the status itself, not the class.

`status_class` is stored rather than derived at read time, which is worth keeping in
mind before trusting it.

| Column | Description |
| --- | --- |
| `account_id` | Agency account number, unique, the join key for every other file |
| `client_id` | The creditor that placed the account, joins to `clients.csv` |
| `client_account_number` | The creditor's own reference for the same debt |
| `original_creditor` | Name of the creditor as it should be disclosed to the consumer |
| `product_type` | What the debt is for, such as `MEDICAL`, `CREDIT_CARD`, `AUTO_DEFICIENCY` |
| `portfolio_batch` | The placement batch the account arrived in |
| `placement_date` | Date the account was placed with the agency |
| `charge_off_date` | Date the creditor charged the debt off |
| `date_of_first_delinquency` | Date the account first went past due |
| `account_status` | Current detailed status |
| `status_class` | Rollup of the status: `OPEN`, `PTP`, `SENSITIVE` or `CLOSED` |
| `status_date` | Date the account last changed status |
| `closed_date` | Date the account was closed, blank while it is open |
| `close_reason` | Free text reason recorded at closure |
| `original_balance` | Balance at charge off, as reported by the creditor |
| `placement_balance` | Balance when the account was placed |
| `principal_balance` | Portion of the current balance that is principal |
| `interest_accrued` | Post placement interest, only where the client contract allows it |
| `fees_accrued` | Collection fees and court costs, only where the contract allows them |
| `adjustment_amount` | Balance waived, negative, most often from a settlement |
| `current_balance` | What the consumer owes today |
| `total_paid` | Total posted payments on the account |
| `interest_rate_pct` | Annual rate applied post placement, zero where none applies |
| `last_payment_date` | Date of the most recent posted payment |
| `last_payment_amount` | Amount of that payment |
| `assigned_user_id` | Collector who owns the account, joins to `users.csv` |
| `last_worked_date` | Last date any collector touched the account |
| `next_action_date` | Date the account is queued to be worked again |
| `collectability_score` | Internal score from 1 to 99, higher means more likely to pay |
| `credit_reported_flag` | Whether the agency reports this account to the bureaus |
| `created_timestamp` | When the account row was created |
| `last_updated_timestamp` | When the account row last changed |
| `first_name`, `middle_initial`, `last_name`, `name_suffix` | Consumer name |
| `ssn` | Consumer Social Security number, synthetic |
| `date_of_birth` | Consumer date of birth |
| `address_line1`, `address_line2`, `city`, `state`, `zip_code` | Consumer address, US only |
| `address_status` | `VERIFIED`, `UNVERIFIED` or `BAD` |
| `phone_home`, `phone_cell`, `phone_work` | Consumer phone numbers |
| `email` | Consumer email address |
| `employer_name` | Employer, where known |
| `do_not_call_flag` | Consumer asked not to be called by phone |
| `cease_desist_flag` | Consumer asked for all contact to stop |
| `attorney_represented_flag`, `attorney_name` | Consumer is represented by counsel |
| `dispute_flag`, `dispute_date` | Consumer disputed the debt |
| `bankruptcy_case_number`, `bankruptcy_chapter`, `bankruptcy_filed_date` | Populated for accounts in bankruptcy status |
| `deceased_date` | Populated for accounts closed because the consumer died |

### notes.csv

The activity log, and the largest file. Every call attempt, letter, payment, status
change and compliance review lands here.

| Column | Description |
| --- | --- |
| `note_id` | Unique note identifier |
| `account_id` | Account the note belongs to |
| `note_datetime` | Timestamp of the activity, `YYYY-MM-DD HH:MM:SS` |
| `user_id` | Who logged it, joins to `users.csv`, `1001` is the system account |
| `contact_type` | `OUTBOUND_CALL`, `INBOUND_CALL`, `LETTER`, `EMAIL`, `SMS`, `SKIP_TRACE`, `PAYMENT`, `ARRANGEMENT`, `LEGAL`, `REVIEW`, `SYSTEM` |
| `action_code` | What was attempted, such as `DIAL` or `LETTER_SENT` |
| `result_code` | What happened, such as `NO_ANSWER`, `RPC`, `PROMISE_TO_PAY`, `PAYMENT_NSF` |
| `phone_dialed` | Number dialed, on call notes |
| `follow_up_date` | Date the collector committed to follow up |
| `is_system_generated` | `Y` for automated notes, `N` for notes a person typed |
| `note_text` | Free text. May contain commas, quotation marks and line breaks |

### payments.csv

One row per payment transaction. A payment that was returned or reversed stays in the
file with a status that says so, so summing the amount column without filtering on
`payment_status` overstates collections.

| Column | Description |
| --- | --- |
| `payment_id` | Unique payment identifier |
| `account_id` | Account the payment was applied to |
| `arrangement_id` | Arrangement it was made under, blank for one off payments |
| `payment_date` | Date the consumer paid |
| `posted_date` | Date the agency posted it |
| `payment_amount` | Amount paid |
| `payment_method` | `ACH`, `DEBIT_CARD`, `CREDIT_CARD`, `CHECK`, `MONEY_ORDER`, `WESTERN_UNION`, `CASH`, `ONLINE_PORTAL` |
| `payment_type` | `PAYMENT`, `ARRANGEMENT_PAYMENT` or `SETTLEMENT_PAYMENT` |
| `payment_status` | `POSTED`, `NSF_RETURNED` or `REVERSED` |
| `reversal_date`, `reversal_reason` | Populated when the payment did not stick |
| `check_number` | For checks and money orders |
| `transaction_reference` | Processor reference |
| `applied_to_principal`, `applied_to_interest`, `applied_to_fees` | How the payment was allocated |
| `agency_fee_amount` | The agency's contingency fee on this payment |
| `client_remit_amount` | What was owed back to the client |
| `remit_date` | When it was remitted |
| `received_by_user_id` | Who took the payment |
| `batch_id` | Posting batch |

### payment_arrangements.csv

Installment plans and settlement agreements. An account can have more than one over its
life, for example a plan that broke and a later replacement.

| Column | Description |
| --- | --- |
| `arrangement_id` | Unique arrangement identifier |
| `account_id` | Account the arrangement covers |
| `created_date`, `created_by_user_id`, `approved_by_user_id` | Who set it up and when |
| `arrangement_type` | `INSTALLMENT`, `SETTLEMENT`, `POST_DATED` or `PIF_SCHEDULED` |
| `arrangement_status` | `ACTIVE`, `COMPLETED`, `BROKEN` or `CANCELLED` |
| `total_amount` | Total the consumer agreed to pay |
| `down_payment_amount` | Up front payment, zero where there was none |
| `installment_amount` | Amount of each scheduled payment |
| `number_of_installments` | How many payments were scheduled |
| `payment_frequency` | `WEEKLY`, `BIWEEKLY`, `SEMIMONTHLY` or `MONTHLY` |
| `first_payment_date`, `next_payment_date`, `final_payment_date` | Schedule dates |
| `payments_made`, `payments_missed` | Counters maintained by the system |
| `amount_paid_to_date`, `balance_remaining` | Money counters |
| `payment_method_on_file`, `auto_debit_flag` | How payments are collected |
| `broken_date`, `broken_reason` | Populated when the arrangement failed |
| `settlement_pct` | Percentage of the balance accepted, on settlements |
| `last_updated_timestamp` | When the row last changed |

### clients.csv

The creditors placing accounts. The contract terms here govern what the agency may do,
so this file is worth reading before drawing conclusions about the accounts.

| Column | Description |
| --- | --- |
| `client_id` | Unique client identifier |
| `client_code`, `client_name`, `industry`, `primary_product_type` | Who they are |
| `contact_name`, `contact_email`, `contact_phone` | Client contact |
| `address_line1`, `city`, `state`, `zip_code` | Client address |
| `contract_start_date`, `contract_end_date` | Contract window |
| `contingency_rate_pct` | Percentage of collections the agency keeps |
| `allows_interest`, `interest_rate_pct` | Whether post placement interest may be added |
| `allows_fees` | Whether collection fees may be added |
| `allows_settlement`, `min_settlement_pct` | Whether settlements are permitted, and the floor |
| `client_status` | `ACTIVE` or `INACTIVE` |

### users.csv

Agency staff. Collectors leave, and the accounts they were working do not always follow.

| Column | Description |
| --- | --- |
| `user_id` | Unique user identifier. `1001` is the system account that writes automated notes |
| `username`, `first_name`, `last_name`, `email` | Identity |
| `role` | `COLLECTOR`, `SR_COLLECTOR`, `TEAM_LEAD`, `SUPERVISOR`, `MANAGER`, `ADMIN`, `COMPLIANCE`, `LEGAL_SPECIALIST`, `SYSTEM` |
| `team` | `ALPHA`, `BRAVO`, `CHARLIE`, `EARLY_OUT` or `LEGAL` |
| `manager_user_id` | Who they report to |
| `phone_extension` | Desk extension |
| `hire_date`, `termination_date` | Employment dates |
| `user_status` | `ACTIVE`, `INACTIVE`, `LOA` or `TERMINATED` |
| `monthly_goal_amount` | Collection goal, for roles that carry one |
| `last_login_date` | Last time they signed in |

## A word of warning about the data

This set was built to look like a real production database that has been running for
five years, which means it has the flaws of one. Values are missing, some records
contradict each other, some records contradict the notes written about them, and a few
are impossible on their face. That is intentional. Assume nothing is clean until it has
been checked, and expect that the answer to a question often depends on how the messy
rows are treated.

A handful of fields are dependable. Every account has an `account_id`,
`client_account_number`, `placement_date`, `account_status`, `status_date`,
`original_balance` and `placement_balance`, and those are the safest things to anchor on.

## What is in this repository

| Path | What it is |
| --- | --- |
| `generate.py` | The generator. Builds every file and writes the answer key |
| `refdata.py` | Name, street and city pools, plus real US city, state and ZIP combinations |
| `validate.py` | Sanity checks over whatever was generated |
| `ANSWER_KEY.md` | Facilitator key, written by the generator on every run |
| `data/` | Generated output, not tracked here |

## A note for facilitators

`ANSWER_KEY.md` lists every planted defect with its counts and sample record ids, and
it is regenerated on each run so it can never drift from the data. It is committed here
because the generator itself is public, and `generate.py` describes every defect inline
anyway, so there is nothing to hide by leaving the key out.

That does mean anyone who finds this repository can read the answers. If you want
participants to discover the issues themselves, hand them the six CSV files rather than
a link to this repository.

## License

Apache License 2.0. See [LICENSE](LICENSE).

The data the generator produces is synthetic and describes no real person or business.
Use it however you like, with or without attribution.
