# Facilitator answer key

Do not hand this file to participants. It lists every defect planted in the data set, generated directly by `generate.py`, so it stays in step with the files.

## Volumes

| File | Rows |
| --- | ---: |
| clients.csv | 16 |
| users.csv | 49 |
| accounts.csv | 10,000 (3,477 closed, 34.8%) |
| payments.csv | 13,339 |
| payment_arrangements.csv | 2,276 |
| notes.csv | 197,573 |

## Identifier safety

Every phone number in the set uses the 555 exchange and every SSN breaks an SSA issuance rule (area 000 / 666 / 900-999, group 00, or serial 0000), so none of them can reach or identify a real person. Defect A11 is junk typed into the SSN field, not an invalid SSN, because every SSN here is already unissuable.

## The propensity model

Liquidation in this data is not random. Every account carries a latent propensity drawn from the fixed logistic model below, and that score decides whether it pays, how much and how often, what status it lands in, how its right party contacts go, and what `collectability_score` it carries.

The coefficients are constants in `generate.py`, not seeded, so any two data sets share this model and differ only in noise. A scorecard fitted on one should hold its shape on the other. Run `python ab_check.py` to see that measured.

Log-odds that an account ever pays anything:

| Term | Coefficient |
| --- | ---: |
| Intercept | -0.95 |
| Debt age at placement, per year from charge-off to placement | -0.55 |
| Placement balance, per 10x above a $250 base | -0.52 |
| Consumer paid the original creditor at some point | +0.75 |
| ... and how recently, decaying to zero over 24 months | +0.60 |
| Cell phone on file | +0.35 |
| Home phone on file | +0.15 |
| Address status VERIFIED | +0.25 |
| Address status BAD | -0.40 |
| Product type UTILITY | +0.35 |
| Product type TELECOM | +0.30 |
| Product type MEDICAL | +0.25 |
| Product type DENTAL | +0.15 |
| Product type VETERINARY | +0.15 |
| Product type GYM_MEMBERSHIP | +0.10 |
| Product type RETAIL_CARD | +0.05 |
| Product type CREDIT_CARD | +0.00 |
| Product type PERSONAL_LOAN | -0.15 |
| Product type RENTAL | -0.20 |
| Product type SUBROGATION | -0.25 |
| Product type AUTO_DEFICIENCY | -0.35 |
| Product type STUDENT_LOAN | -0.40 |
| Gaussian noise, standard deviation | 0.85 |

That latent score is then multiplied by an exposure term, `1 - exp(-days_on_book / 165)`, because an account placed last month has not had time to show what it is worth. Debt age and time on book are separate things here, and conflating them is the most common way to get this analysis wrong.

In this data set 2,872 accounts (28.7%) paid something.

Two modeling exercises this supports:

1. **Placement scoring.** Predict liquidation using only what was known at placement: debt age, balance, client last payment, product type, contact data. This is the model the table above describes.
2. **In-treatment scoring.** Predict payment after day 90 using agency activity in the first 90 days, such as whether a right party contact happened or a promise to pay was logged. Those features are far stronger, and they are partly self fulfilling, so they only make sense with a time split. Without one they leak.

## Fields that are always reliable

These are populated on every account row and are internally consistent, so participants can anchor on them: `account_id`, `client_account_number`, `placement_date`, `account_status`, `status_date`, `original_balance`, `placement_balance`. Note that `placement_balance` carries a dollar sign on twelve rows (defect A21); the value itself is still correct.

## Planted defects

### accounts

**A1 - address_line1, city, state, zip_code** (550 rows)

Missing or incomplete consumer addresses, including literal 'UNKNOWN' text values.

*About 6% of accounts. Note the several different shapes of 'missing'.*

Sample ids: 500005, 500030, 500036, 500057, 500062, 500075

**A2 - zip_code** (484 rows)

Northeast ZIP codes stored with the leading zero stripped (e.g. 2108 instead of 02108).

*Classic spreadsheet round-trip damage. Look for zip_code shorter than 5 characters.*

Sample ids: 505500, 503373, 509620, 500733, 500125, 503167

**A3 - state, zip_code** (35 rows)

ZIP code does not fall in the stated state.

Sample ids: 509410, 506925, 508286, 500841, 509158, 505489

**A4 - current_balance** (40 rows)

current_balance exceeds placement_balance on clients whose contract allows no interest and no fees.

*Join accounts to clients on client_id and compare against allows_interest / allows_fees.*

Sample ids: 509955, 506937, 504676, 505582, 502129, 509037

**A5 - account_status, current_balance** (25 rows)

Accounts closed as PAID_IN_FULL or SETTLED_IN_FULL that still show a non-zero balance.

Sample ids: 508635, 507889, 506604, 509806, 504212, 506237

**A6 - current_balance** (12 rows)

Negative current_balance from unrefunded overpayments.

Sample ids: 501976, 509106, 507530, 505056, 509950, 506383

**A7 - bankruptcy_case_number, bankruptcy_chapter, bankruptcy_filed_date** (18 rows)

BANKRUPTCY accounts missing the case number, chapter or filing date.

*These fields should be fully populated for every BANKRUPTCY account.*

Sample ids: 508960, 502188, 505449, 502978, 501093, 500036

**A8 - bankruptcy_case_number, account_status** (10 rows)

Bankruptcy case data present on accounts whose status is not BANKRUPTCY, so collection activity continued.

*The reverse of A7, and the more dangerous direction.*

Sample ids: 505942, 500042, 507114, 505511, 507366, 501139

**A9a - deceased_date** (7 rows)

DECEASED accounts with no date of death recorded.

Sample ids: 509152, 503428, 507315, 509316, 508035, 507472

**A9b - deceased_date, placement_date** (5 rows)

Date of death precedes the placement date; the account should never have been placed.

Sample ids: 507648, 507735, 509591, 507550, 509974

**A10a - date_of_birth** (8 rows)

Date of birth implies the consumer is under 18.

Sample ids: 509729, 505397, 503449, 504506, 505112, 509025

**A10b - date_of_birth** (6 rows)

Date of birth implies an age over 110.

Sample ids: 501477, 503002, 505010, 506572, 506073, 501522

**A11 - ssn** (20 rows)

Placeholder and malformed junk in the SSN field: all zeros, repeated digits, sequential digits, masked values, free text, and values that are not nine digits.

*Every SSN in this file is deliberately unissuable, so these stand out by being the wrong shape rather than by being invalid.*

Sample ids: 509271, 503749, 502505, 501120, 501875, 506872

**A12 - ssn** (14 rows)

Fourteen accounts with different consumer names share a single SSN (975-37-1630).

*Group by ssn and count distinct last_name.*

Sample ids: 508335, 508465, 502451, 508601, 507788, 503143

**A13 - phone_home, phone_cell** (60 rows)

Placeholder or malformed phone numbers, plus four different phone formats across the file depending on which client sent the account.

*The formatting inconsistency is by client_id; the junk values are scattered.*

Sample ids: 502446, 503939, 502952, 507941, 509096, 504663

**A14 - email** (90 rows)

Invalid or placeholder email addresses.

Sample ids: 501302, 504867, 500695, 505777, 508633, 503926

**A15 - client_id, client_account_number** (22 rows)

The same creditor account placed twice under two different account_ids, with slightly different placement dates and balances.

*Group by client_id + client_account_number having count > 1. Sample values are id pairs.*

Sample ids: 507676/507976, 509126/508114, 505925/500115, 506085/509300, 502323/503080, 507724/508586

**A16a - assigned_user_id** (120 rows)

Open accounts assigned to users whose user_status is TERMINATED.

*Join accounts to users on assigned_user_id and filter on user_status.*

Sample ids: 505316, 506429, 500060, 507464, 501412, 507318

**A16b - assigned_user_id** (9 rows)

assigned_user_id values that do not exist in users.csv.

Sample ids: 500689, 506408, 500366, 507660, 502638, 502949

**A17 - client_id** (4 rows)

client_id values with no matching row in clients.csv.

Sample ids: 502469, 505756, 500664, 501389

**A18 - first_name, last_name** (140 rows)

Name hygiene problems: mixed casing, leading and trailing whitespace, suffixes stuffed into last_name, stray punctuation.

Sample ids: 507090, 502063, 507417, 507210, 503664, 507342

**A19a - charge_off_date, placement_date** (15 rows)

charge_off_date falls after placement_date; an account cannot be placed before it charges off.

Sample ids: 501533, 505387, 505858, 509822, 502212, 505756

**A19b - date_of_first_delinquency, charge_off_date** (10 rows)

date_of_first_delinquency falls after charge_off_date, which distorts credit reporting and statute math.

Sample ids: 506129, 501383, 505432, 505420, 507853, 509423

**A20a - last_payment_date, last_payment_amount** (30 rows)

Accounts showing a last payment when payments.csv holds no payment for them at all.

*The single most useful cross-file reconciliation in the set.*

Sample ids: 503446, 508438, 508462, 500243, 508467, 502404

**A20b - total_paid** (50 rows)

accounts.total_paid does not equal the sum of POSTED payments in payments.csv.

Sample ids: 509467, 502084, 504827, 502875, 508280, 508631

**A21 - current_balance, placement_balance** (12 rows)

A handful of balance cells carry a dollar sign and thousands separators, so the column loads as text instead of a number.

*Whoever loads the file naively will get a type error or silent string sort here.*

Sample ids: 501765, 507628, 500034, 504221, 504017, 500753

**A22 - status_date, placement_date** (9 rows)

status_date precedes placement_date.

Sample ids: 508453, 507643, 501019, 509993, 507979, 505780

**A23 - next_action_date, account_status** (40 rows)

Closed accounts still carrying a future next_action_date, so they stay in collector queues.

Sample ids: 505908, 508026, 508482, 507513, 507609, 505255

**A24 - employer_name, address_line2, middle_initial, phone_work, email** (70 rows)

Empty values written five different ways: blank, NULL, N/A, n/a, -, UNKNOWN, none.

*Anything counting nulls will undercount unless these are normalized first.*

Sample ids: 502902, 500016, 507534, 509833, 501816, 501620

**A25 - state** (6 rows)

Invalid or non-standard state codes.

Sample ids: 504335, 507757, 509225, 507823, 503487, 506561

**A26 - ssn, last_name** (30 rows)

Not a defect: roughly 30 consumers hold multiple accounts across different clients. The set rewards recognizing this before deduplicating.

*Distinguish these from the true duplicates in A15.*

Sample ids: 500647, 502453, 500125, 506923, 502117, 501005

**A27 - total_paid, adjustment_amount** (20 rows)

Settlements accepted for less than the client's contractual min_settlement_pct. The account was closed as SETTLED_IN_FULL and the rest of the balance waived without authority.

*Easiest to see as payment_arrangements.settlement_pct below clients.min_settlement_pct; otherwise compare total_paid against placement_balance + interest + fees.*

Sample ids: 509129, 507486, 504712, 507419, 506791, 508493

**A28 - account_status, client_id** (15 rows)

Accounts closed as SETTLED_IN_FULL under clients whose contract sets allows_settlement = N.

*Join accounts to clients and check account_status against allows_settlement.*

Sample ids: 501425, 504932, 506750, 508266, 505327, 500918

**A29 - status_class, account_status** (30 rows)

status_class disagrees with account_status. Most are closed accounts still classed as OPEN or PTP, so they inflate open inventory and stay in work queues; a few are open accounts classed CLOSED, so they disappear from reporting.

*status_class is a denormalized rollup of account_status. Rebuild it from the status and compare, rather than trusting the stored value.*

Sample ids: 506003, 509877, 506260, 503079, 505818, 508499

**A30 - client_last_payment_date, placement_date** (40 rows)

The last payment to the original creditor is dated after placement, so the consumer paid the client directly while the agency kept collecting. The agency balance was never reduced.

*Real and expensive: it causes double collection and client disputes. Compare client_last_payment_date against placement_date.*

Sample ids: 504484, 505496, 504743, 503342, 503470, 501650

### payments

**P1 - account_id** (12 rows)

Payments referencing account_ids that are not in accounts.csv.

Sample ids: 9005521, 9006794, 9001567, 9013193, 9010105, 9001905

**P2 - payment_date** (25 rows)

Payments dated after the account was closed, including payments taken on bankruptcy and deceased accounts.

*Join to accounts.closed_date. Some of these are compliance problems, not just data problems.*

Sample ids: 9000598, 9009559, 9007004, 9009235, 9002014, 9006731

**P3 - payment_amount** (10 rows)

Posted payments with a zero or negative amount.

Sample ids: 9012454, 9003270, 9007474, 9000344, 9000251, 9011535

**P4 - payment_id, transaction_reference** (15 rows)

Duplicate payment rows: identical account, date, amount and transaction reference under two payment_ids.

*Sample values are id pairs. Also inflates total collections if counted naively.*

Sample ids: 9008762/9800000, 9009451/9800001, 9004885/9800002, 9003724/9800003, 9007492/9800004, 9009173/9800005

**P5 - payment_date** (6 rows)

Payment dates in the future.

Sample ids: 9012810, 9003083, 9004302, 9007542, 9003329, 9001780

**P6 - received_by_user_id** (20 rows)

Missing or invalid receiving user on the payment.

Sample ids: 9000334, 9009610, 9002041, 9009906, 9000165, 9010251

**P7 - payment_date, posted_date** (5 rows)

Payments posted before the account was ever placed with the agency.

Sample ids: 9010648, 9008950, 9006252, 9010258, 9012633

**P8 - payment_method** (18 rows)

Payment method spelled several different ways for the same method.

*Grouping by payment_method without normalizing splits the same method across buckets.*

Sample ids: 9011052, 9005581, 9004780, 9013152, 9006936, 9009882

### payment_arrangements

**R1 - arrangement_status, next_payment_date** (60 rows)

Arrangements still marked ACTIVE whose next payment was due months ago; they are broken but nothing reflects it.

*These accounts are also still counted in 'accounts on a plan' reporting.*

Sample ids: 701016, 702147, 702131, 700609, 700689, 701801

**R2 - arrangement_status** (18 rows)

Active arrangements, with a future payment still scheduled, sitting on accounts that are already closed. Several of these accounts are closed as bankruptcy or deceased.

*Join arrangements to accounts.closed_date.*

Sample ids: 700906, 701209, 700701, 701892, 701570, 701405

**R3 - installment_amount, number_of_installments, total_amount** (30 rows)

installment_amount times number_of_installments does not reconcile to total_amount.

Sample ids: 700689, 701015, 700515, 700068, 702017, 700403

**R4 - payments_made, amount_paid_to_date** (12 rows)

Arrangements claiming payments were made when payments.csv has none for that arrangement.

Sample ids: 701145, 701407, 702047, 701951, 700785, 701452

**R5 - account_id, arrangement_status** (10 rows)

Two simultaneously ACTIVE arrangements on the same account.

*Sample values are account_ids. Group by account_id where status = ACTIVE.*

Sample ids: 501025, 501168, 500739, 502966, 503081, 500571

**R6 - arrangement_status, broken_date** (8 rows)

broken_date and broken_reason populated while arrangement_status is still ACTIVE.

Sample ids: 701715, 700935, 700467, 700348, 700565, 701493

### notes

**N1 - user_id** (38 rows)

Notes written by user_id 9999, which does not exist in users.csv.

*Left join notes to users on user_id.*

Sample ids: 500250, 500591, 501205, 501407, 501501, 501920

**N2 - note_datetime** (25 rows)

Notes dated before the account's placement_date.

Sample ids: 500420, 501062, 501747, 502374, 502637, 503435

**N3 - note_datetime** (115 rows)

Outbound call notes timestamped outside 8:00am-9:00pm, an FDCPA calling-window problem.

*Filter contact_type = OUTBOUND_CALL and check the hour part of note_datetime.*

Sample ids: 500004, 500103, 500254, 500270, 500309, 500498

**N4a - note_text** (35 rows)

Notes documenting a cease and desist request where accounts.cease_desist_flag is still N.

*Search note_text for 'cease and desist' and compare the account flag.*

Sample ids: 500181, 500861, 501199, 501401, 501454, 501478

**N4b - note_text** (25 rows)

Notes documenting attorney representation where accounts.attorney_represented_flag is still N.

Sample ids: 500862, 501246, 502474, 503000, 503069, 503529

**N5 - note_text** (50 rows)

Exact duplicate notes: same account, timestamp and text under two note_ids.

Sample ids: 500245, 500488, 500601, 500730, 500768, 500999

**N6 - note_text** (60 rows)

Note text containing embedded newlines, quotes and commas. Correct per RFC 4180 but it breaks naive line-by-line parsing.

*notes.csv has far more physical lines than records.*

Sample ids: 500042, 500062, 500116, 500248, 500574, 500710

**N7 - note_datetime** (30 rows)

Collection calls logged after the account was closed, including bankruptcy and deceased accounts.

Sample ids: 500369, 500400, 500495, 500645, 500690, 500723

**N8 - note_text** (7 rows)

Third-party disclosure: the balance and creditor were revealed to someone other than the consumer.

*A compliance issue rather than a structural one.*

Sample ids: 500538, 500739, 501507, 502700, 503287, 505742

### clients

**C1 - client_name** (2 rows)

Near-duplicate client records for the same creditor (Mercy Regional Health System / Mercy Regional Health Sys.), with accounts split across both client_ids.

*Compare account counts and balances by client_name.*

Sample ids: 101, 116

**C2 - contract_end_date** (1 rows)

Client contract ended 2025-03-31 but accounts were placed under it afterward.

*Join accounts.placement_date against clients.contract_end_date.*

Sample ids: 111

**C3 - contact_email** (1 rows)

Client record missing a contact email.

Sample ids: 110

### users

**U1 - username** (2 rows)

Two different user_ids share one username.

Sample ids: 1020, 1021

**U2 - email** (2 rows)

Active users with no email address on file.

Sample ids: 1023, 1024

## Suggested exercises

- Profile every file and produce a data dictionary without being told the schema.
- Reconcile `accounts.total_paid` against the sum of POSTED payments and explain each break.
- Find every account where the notes contradict the compliance flags (A8, N4a, N4b).
- Build a collector performance report from notes and payments, then explain why the numbers are wrong until terminated users and duplicate payments are handled.
- Identify accounts that should never have been worked: bankruptcy, deceased, cease and desist.
- Measure liquidation rate by client and by placement year, and defend the denominator chosen.
- Count how many distinct consumers exist. The answer depends on how A12, A15 and A26 are treated.
- Rebuild status_class from account_status and find the rows where the stored rollup disagrees, then say what that does to an open inventory count.
- Find the FDCPA calling-window violations in the notes (N3).
