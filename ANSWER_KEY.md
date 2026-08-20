# Facilitator answer key

Do not hand this file to participants. It lists every defect planted in the data set, generated directly by `generate.py`, so it stays in step with the files.

## Volumes

| File | Rows |
| --- | ---: |
| clients.csv | 16 |
| users.csv | 49 |
| accounts.csv | 10,000 (3,447 closed, 34.5%) |
| payments.csv | 15,383 |
| payment_arrangements.csv | 2,400 |
| notes.csv | 200,115 |

## Identifier safety

Every phone number in the set uses the 555 exchange and every SSN breaks an SSA issuance rule (area 000 / 666 / 900-999, group 00, or serial 0000), so none of them can reach or identify a real person. Defect A11 is junk typed into the SSN field, not an invalid SSN, because every SSN here is already unissuable.

## Fields that are always reliable

These are populated on every account row and are internally consistent, so participants can anchor on them: `account_id`, `client_account_number`, `placement_date`, `account_status`, `status_date`, `original_balance`, `placement_balance`. Note that `placement_balance` carries a dollar sign on twelve rows (defect A21); the value itself is still correct.

## Planted defects

### accounts

**A1 - address_line1, city, state, zip_code** (553 rows)

Missing or incomplete consumer addresses, including literal 'UNKNOWN' text values.

*About 6% of accounts. Note the several different shapes of 'missing'.*

Sample ids: 500011, 500050, 500071, 500094, 500105, 500117

**A2 - zip_code** (511 rows)

Northeast ZIP codes stored with the leading zero stripped (e.g. 2108 instead of 02108).

*Classic spreadsheet round-trip damage. Look for zip_code shorter than 5 characters.*

Sample ids: 509440, 502485, 507590, 502713, 506864, 504826

**A3 - state, zip_code** (35 rows)

ZIP code does not fall in the stated state.

Sample ids: 508661, 503378, 501938, 502295, 503972, 505227

**A4 - current_balance** (40 rows)

current_balance exceeds placement_balance on clients whose contract allows no interest and no fees.

*Join accounts to clients on client_id and compare against allows_interest / allows_fees.*

Sample ids: 509003, 504487, 506115, 509884, 504538, 509774

**A5 - account_status, current_balance** (25 rows)

Accounts closed as PAID_IN_FULL or SETTLED_IN_FULL that still show a non-zero balance.

Sample ids: 505910, 504872, 501052, 506922, 504321, 507294

**A6 - current_balance** (12 rows)

Negative current_balance from unrefunded overpayments.

Sample ids: 504822, 508616, 502051, 504095, 507962, 502006

**A7 - bankruptcy_case_number, bankruptcy_chapter, bankruptcy_filed_date** (18 rows)

BANKRUPTCY accounts missing the case number, chapter or filing date.

*These fields should be fully populated for every BANKRUPTCY account.*

Sample ids: 502087, 504923, 503377, 500293, 505106, 507774

**A8 - bankruptcy_case_number, account_status** (10 rows)

Bankruptcy case data present on accounts whose status is not BANKRUPTCY, so collection activity continued.

*The reverse of A7, and the more dangerous direction.*

Sample ids: 500280, 506360, 507565, 509477, 507187, 508858

**A9a - deceased_date** (7 rows)

DECEASED accounts with no date of death recorded.

Sample ids: 506485, 507668, 500378, 509728, 506682, 508317

**A9b - deceased_date, placement_date** (5 rows)

Date of death precedes the placement date; the account should never have been placed.

Sample ids: 503165, 504579, 504932, 503661, 505235

**A10a - date_of_birth** (8 rows)

Date of birth implies the consumer is under 18.

Sample ids: 505928, 500742, 508690, 505822, 509346, 501682

**A10b - date_of_birth** (6 rows)

Date of birth implies an age over 110.

Sample ids: 503189, 506750, 500024, 509925, 500381, 503335

**A11 - ssn** (20 rows)

Placeholder and malformed junk in the SSN field: all zeros, repeated digits, sequential digits, masked values, free text, and values that are not nine digits.

*Every SSN in this file is deliberately unissuable, so these stand out by being the wrong shape rather than by being invalid.*

Sample ids: 501757, 501584, 505492, 506933, 500558, 502954

**A12 - ssn** (14 rows)

Fourteen accounts with different consumer names share a single SSN (967-16-9529).

*Group by ssn and count distinct last_name.*

Sample ids: 500345, 507395, 501509, 502184, 509945, 505870

**A13 - phone_home, phone_cell** (60 rows)

Placeholder or malformed phone numbers, plus four different phone formats across the file depending on which client sent the account.

*The formatting inconsistency is by client_id; the junk values are scattered.*

Sample ids: 502038, 508371, 508751, 507704, 508793, 507124

**A14 - email** (90 rows)

Invalid or placeholder email addresses.

Sample ids: 507378, 503216, 501180, 501873, 506874, 500438

**A15 - client_id, client_account_number** (22 rows)

The same creditor account placed twice under two different account_ids, with slightly different placement dates and balances.

*Group by client_id + client_account_number having count > 1. Sample values are id pairs.*

Sample ids: 504210/501613, 503003/504294, 507254/504945, 504137/509274, 507434/506132, 507504/500861

**A16a - assigned_user_id** (120 rows)

Open accounts assigned to users whose user_status is TERMINATED.

*Join accounts to users on assigned_user_id and filter on user_status.*

Sample ids: 505285, 503227, 500287, 508817, 501475, 502476

**A16b - assigned_user_id** (9 rows)

assigned_user_id values that do not exist in users.csv.

Sample ids: 502344, 500498, 507244, 509204, 502069, 507495

**A17 - client_id** (4 rows)

client_id values with no matching row in clients.csv.

Sample ids: 500993, 504904, 500548, 500623

**A18 - first_name, last_name** (140 rows)

Name hygiene problems: mixed casing, leading and trailing whitespace, suffixes stuffed into last_name, stray punctuation.

Sample ids: 509819, 506443, 505269, 502827, 501114, 506841

**A19a - charge_off_date, placement_date** (15 rows)

charge_off_date falls after placement_date; an account cannot be placed before it charges off.

Sample ids: 500173, 509106, 500317, 509653, 504362, 500069

**A19b - date_of_first_delinquency, charge_off_date** (10 rows)

date_of_first_delinquency falls after charge_off_date, which distorts credit reporting and statute math.

Sample ids: 500179, 503846, 505175, 507998, 503566, 507746

**A20a - last_payment_date, last_payment_amount** (30 rows)

Accounts showing a last payment when payments.csv holds no payment for them at all.

*The single most useful cross-file reconciliation in the set.*

Sample ids: 509987, 507469, 509734, 503990, 502619, 508296

**A20b - total_paid** (50 rows)

accounts.total_paid does not equal the sum of POSTED payments in payments.csv.

Sample ids: 502831, 501179, 505429, 504023, 501928, 502533

**A21 - current_balance, placement_balance** (12 rows)

A handful of balance cells carry a dollar sign and thousands separators, so the column loads as text instead of a number.

*Whoever loads the file naively will get a type error or silent string sort here.*

Sample ids: 502591, 503682, 501788, 507465, 507215, 508253

**A22 - status_date, placement_date** (9 rows)

status_date precedes placement_date.

Sample ids: 501911, 508421, 502681, 505596, 508127, 501657

**A23 - next_action_date, account_status** (40 rows)

Closed accounts still carrying a future next_action_date, so they stay in collector queues.

Sample ids: 503610, 509198, 503460, 506046, 501016, 505172

**A24 - employer_name, address_line2, middle_initial, phone_work, email** (70 rows)

Empty values written five different ways: blank, NULL, N/A, n/a, -, UNKNOWN, none.

*Anything counting nulls will undercount unless these are normalized first.*

Sample ids: 504387, 503330, 509046, 505859, 508075, 507411

**A25 - state** (6 rows)

Invalid or non-standard state codes.

Sample ids: 500354, 508960, 508432, 507216, 508307, 509471

**A26 - ssn, last_name** (30 rows)

Not a defect: roughly 30 consumers hold multiple accounts across different clients. The set rewards recognizing this before deduplicating.

*Distinguish these from the true duplicates in A15.*

Sample ids: 503188, 501618, 506493, 508617, 507327, 508370

**A27 - total_paid, adjustment_amount** (20 rows)

Settlements accepted for less than the client's contractual min_settlement_pct. The account was closed as SETTLED_IN_FULL and the rest of the balance waived without authority.

*Easiest to see as payment_arrangements.settlement_pct below clients.min_settlement_pct; otherwise compare total_paid against placement_balance + interest + fees.*

Sample ids: 509674, 501270, 507635, 500759, 505511, 508618

**A28 - account_status, client_id** (15 rows)

Accounts closed as SETTLED_IN_FULL under clients whose contract sets allows_settlement = N.

*Join accounts to clients and check account_status against allows_settlement.*

Sample ids: 506894, 506143, 506922, 506002, 506086, 507160

**A29 - status_class, account_status** (30 rows)

status_class disagrees with account_status. Most are closed accounts still classed as OPEN or PTP, so they inflate open inventory and stay in work queues; a few are open accounts classed CLOSED, so they disappear from reporting.

*status_class is a denormalized rollup of account_status. Rebuild it from the status and compare, rather than trusting the stored value.*

Sample ids: 505205, 500743, 503147, 501022, 505322, 501957

### payments

**P1 - account_id** (12 rows)

Payments referencing account_ids that are not in accounts.csv.

Sample ids: 9002830, 9006498, 9001227, 9007626, 9006112, 9009804

**P2 - payment_date** (25 rows)

Payments dated after the account was closed, including payments taken on bankruptcy and deceased accounts.

*Join to accounts.closed_date. Some of these are compliance problems, not just data problems.*

Sample ids: 9009929, 9001642, 9013167, 9015025, 9009164, 9001530

**P3 - payment_amount** (10 rows)

Posted payments with a zero or negative amount.

Sample ids: 9002878, 9014233, 9009126, 9002573, 9004453, 9010504

**P4 - payment_id, transaction_reference** (15 rows)

Duplicate payment rows: identical account, date, amount and transaction reference under two payment_ids.

*Sample values are id pairs. Also inflates total collections if counted naively.*

Sample ids: 9011178/9800000, 9002549/9800001, 9002624/9800002, 9003932/9800003, 9012335/9800004, 9011003/9800005

**P5 - payment_date** (6 rows)

Payment dates in the future.

Sample ids: 9004883, 9004539, 9012208, 9012500, 9005648, 9013474

**P6 - received_by_user_id** (20 rows)

Missing or invalid receiving user on the payment.

Sample ids: 9003762, 9011577, 9003708, 9006750, 9004654, 9010168

**P7 - payment_date, posted_date** (5 rows)

Payments posted before the account was ever placed with the agency.

Sample ids: 9004462, 9005941, 9013421, 9007701, 9000192

**P8 - payment_method** (18 rows)

Payment method spelled several different ways for the same method.

*Grouping by payment_method without normalizing splits the same method across buckets.*

Sample ids: 9010076, 9015024, 9006013, 9012387, 9011536, 9004518

### payment_arrangements

**R1 - arrangement_status, next_payment_date** (60 rows)

Arrangements still marked ACTIVE whose next payment was due months ago; they are broken but nothing reflects it.

*These accounts are also still counted in 'accounts on a plan' reporting.*

Sample ids: 700421, 700907, 700651, 700510, 700661, 701533

**R2 - arrangement_status** (18 rows)

Active arrangements, with a future payment still scheduled, sitting on accounts that are already closed. Several of these accounts are closed as bankruptcy or deceased.

*Join arrangements to accounts.closed_date.*

Sample ids: 701083, 701877, 700601, 702207, 702301, 700657

**R3 - installment_amount, number_of_installments, total_amount** (30 rows)

installment_amount times number_of_installments does not reconcile to total_amount.

Sample ids: 702216, 701963, 700343, 700635, 701121, 700938

**R4 - payments_made, amount_paid_to_date** (12 rows)

Arrangements claiming payments were made when payments.csv has none for that arrangement.

Sample ids: 702186, 700928, 701175, 701849, 702212, 702048

**R5 - account_id, arrangement_status** (10 rows)

Two simultaneously ACTIVE arrangements on the same account.

*Sample values are account_ids. Group by account_id where status = ACTIVE.*

Sample ids: 503803, 508922, 508423, 506202, 502693, 501436

**R6 - arrangement_status, broken_date** (8 rows)

broken_date and broken_reason populated while arrangement_status is still ACTIVE.

Sample ids: 700563, 700651, 701070, 700335, 700148, 701681

### notes

**N1 - user_id** (38 rows)

Notes written by user_id 9999, which does not exist in users.csv.

*Left join notes to users on user_id.*

Sample ids: 500105, 500222, 500690, 501128, 501446, 501477

**N2 - note_datetime** (25 rows)

Notes dated before the account's placement_date.

Sample ids: 500347, 500420, 501204, 501826, 501884, 502041

**N3 - note_datetime** (117 rows)

Outbound call notes timestamped outside 8:00am-9:00pm, an FDCPA calling-window problem.

*Filter contact_type = OUTBOUND_CALL and check the hour part of note_datetime.*

Sample ids: 500083, 500120, 500157, 500240, 500261, 500318

**N4a - note_text** (35 rows)

Notes documenting a cease and desist request where accounts.cease_desist_flag is still N.

*Search note_text for 'cease and desist' and compare the account flag.*

Sample ids: 500172, 500243, 500406, 500416, 500419, 500803

**N4b - note_text** (25 rows)

Notes documenting attorney representation where accounts.attorney_represented_flag is still N.

Sample ids: 500057, 500248, 501532, 501564, 501716, 501832

**N5 - note_text** (47 rows)

Exact duplicate notes: same account, timestamp and text under two note_ids.

Sample ids: 500291, 500468, 500800, 500886, 501310, 501418

**N6 - note_text** (60 rows)

Note text containing embedded newlines, quotes and commas. Correct per RFC 4180 but it breaks naive line-by-line parsing.

*notes.csv has far more physical lines than records.*

Sample ids: 500062, 500651, 500717, 500799, 500919, 500945

**N7 - note_datetime** (30 rows)

Collection calls logged after the account was closed, including bankruptcy and deceased accounts.

Sample ids: 500234, 500565, 500571, 500857, 501260, 502313

**N8 - note_text** (7 rows)

Third-party disclosure: the balance and creditor were revealed to someone other than the consumer.

*A compliance issue rather than a structural one.*

Sample ids: 501037, 501848, 502555, 505835, 507641, 508390

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
