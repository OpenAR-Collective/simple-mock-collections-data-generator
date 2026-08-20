# Facilitator answer key

Do not hand this file to participants. It lists every defect planted in the data set, generated directly by `generate.py`, so it stays in step with the files.

## Volumes

| File | Rows |
| --- | ---: |
| clients.csv | 16 |
| users.csv | 49 |
| accounts.csv | 10,000 (3,433 closed, 34.3%) |
| payments.csv | 16,002 |
| payment_arrangements.csv | 2,539 |
| notes.csv | 199,966 |

## Identifier safety

Every phone number in the set uses the 555 exchange and every SSN breaks an SSA issuance rule (area 000 / 666 / 900-999, group 00, or serial 0000), so none of them can reach or identify a real person. Defect A11 is junk typed into the SSN field, not an invalid SSN, because every SSN here is already unissuable.

## Fields that are always reliable

These are populated on every account row and are internally consistent, so participants can anchor on them: `account_id`, `client_account_number`, `placement_date`, `account_status`, `status_date`, `original_balance`, `placement_balance`. Note that `placement_balance` carries a dollar sign on twelve rows (defect A21); the value itself is still correct.

## Planted defects

### accounts

**A1 - address_line1, city, state, zip_code** (541 rows)

Missing or incomplete consumer addresses, including literal 'UNKNOWN' text values.

*About 6% of accounts. Note the several different shapes of 'missing'.*

Sample ids: 500047, 500068, 500099, 500105, 500140, 500154

**A2 - zip_code** (476 rows)

Northeast ZIP codes stored with the leading zero stripped (e.g. 2108 instead of 02108).

*Classic spreadsheet round-trip damage. Look for zip_code shorter than 5 characters.*

Sample ids: 505793, 503566, 507147, 502186, 509674, 506244

**A3 - state, zip_code** (35 rows)

ZIP code does not fall in the stated state.

Sample ids: 505071, 501838, 500046, 504792, 501083, 507475

**A4 - current_balance** (40 rows)

current_balance exceeds placement_balance on clients whose contract allows no interest and no fees.

*Join accounts to clients on client_id and compare against allows_interest / allows_fees.*

Sample ids: 508850, 505484, 502726, 509957, 509372, 503388

**A5 - account_status, current_balance** (25 rows)

Accounts closed as PAID_IN_FULL or SETTLED_IN_FULL that still show a non-zero balance.

Sample ids: 501690, 503478, 502640, 504055, 507288, 508482

**A6 - current_balance** (12 rows)

Negative current_balance from unrefunded overpayments.

Sample ids: 500855, 503806, 506548, 506814, 506707, 501214

**A7 - bankruptcy_case_number, bankruptcy_chapter, bankruptcy_filed_date** (18 rows)

BANKRUPTCY accounts missing the case number, chapter or filing date.

*These fields should be fully populated for every BANKRUPTCY account.*

Sample ids: 508099, 507107, 507779, 506110, 504851, 504245

**A8 - bankruptcy_case_number, account_status** (10 rows)

Bankruptcy case data present on accounts whose status is not BANKRUPTCY, so collection activity continued.

*The reverse of A7, and the more dangerous direction.*

Sample ids: 507217, 507076, 507504, 508234, 500308, 500787

**A9a - deceased_date** (7 rows)

DECEASED accounts with no date of death recorded.

Sample ids: 509695, 504859, 505606, 507304, 507512, 509380

**A9b - deceased_date, placement_date** (5 rows)

Date of death precedes the placement date; the account should never have been placed.

Sample ids: 506323, 508514, 505332, 500297, 504843

**A10a - date_of_birth** (8 rows)

Date of birth implies the consumer is under 18.

Sample ids: 502852, 504975, 500701, 506604, 503257, 503442

**A10b - date_of_birth** (6 rows)

Date of birth implies an age over 110.

Sample ids: 508343, 503238, 503901, 502670, 505453, 500788

**A11 - ssn** (20 rows)

Placeholder and malformed junk in the SSN field: all zeros, repeated digits, sequential digits, masked values, free text, and values that are not nine digits.

*Every SSN in this file is deliberately unissuable, so these stand out by being the wrong shape rather than by being invalid.*

Sample ids: 502971, 500517, 506903, 501379, 507710, 505511

**A12 - ssn** (14 rows)

Fourteen accounts with different consumer names share a single SSN (982-39-0784).

*Group by ssn and count distinct last_name.*

Sample ids: 501856, 503207, 500113, 506596, 504966, 508202

**A13 - phone_home, phone_cell** (60 rows)

Placeholder or malformed phone numbers, plus four different phone formats across the file depending on which client sent the account.

*The formatting inconsistency is by client_id; the junk values are scattered.*

Sample ids: 507603, 504920, 508449, 504585, 508519, 503786

**A14 - email** (90 rows)

Invalid or placeholder email addresses.

Sample ids: 501127, 502851, 504429, 505194, 502105, 503199

**A15 - client_id, client_account_number** (22 rows)

The same creditor account placed twice under two different account_ids, with slightly different placement dates and balances.

*Group by client_id + client_account_number having count > 1. Sample values are id pairs.*

Sample ids: 502095/500291, 506744/501940, 506509/500806, 507320/501580, 500760/509867, 501536/503097

**A16a - assigned_user_id** (120 rows)

Open accounts assigned to users whose user_status is TERMINATED.

*Join accounts to users on assigned_user_id and filter on user_status.*

Sample ids: 503686, 508946, 506464, 505263, 504826, 502177

**A16b - assigned_user_id** (9 rows)

assigned_user_id values that do not exist in users.csv.

Sample ids: 505076, 507407, 501039, 501243, 503638, 504407

**A17 - client_id** (4 rows)

client_id values with no matching row in clients.csv.

Sample ids: 508354, 501803, 505188, 507342

**A18 - first_name, last_name** (140 rows)

Name hygiene problems: mixed casing, leading and trailing whitespace, suffixes stuffed into last_name, stray punctuation.

Sample ids: 508193, 507874, 504637, 500941, 506770, 509799

**A19a - charge_off_date, placement_date** (15 rows)

charge_off_date falls after placement_date; an account cannot be placed before it charges off.

Sample ids: 500927, 500121, 502906, 507341, 503039, 507284

**A19b - date_of_first_delinquency, charge_off_date** (10 rows)

date_of_first_delinquency falls after charge_off_date, which distorts credit reporting and statute math.

Sample ids: 505244, 506435, 503496, 501833, 502072, 501531

**A20a - last_payment_date, last_payment_amount** (30 rows)

Accounts showing a last payment when payments.csv holds no payment for them at all.

*The single most useful cross-file reconciliation in the set.*

Sample ids: 507520, 504508, 508779, 503659, 505235, 505607

**A20b - total_paid** (50 rows)

accounts.total_paid does not equal the sum of POSTED payments in payments.csv.

Sample ids: 502961, 501894, 500158, 508490, 505299, 507249

**A21 - current_balance, placement_balance** (12 rows)

A handful of balance cells carry a dollar sign and thousands separators, so the column loads as text instead of a number.

*Whoever loads the file naively will get a type error or silent string sort here.*

Sample ids: 505023, 507355, 503244, 508071, 507298, 501979

**A22 - status_date, placement_date** (9 rows)

status_date precedes placement_date.

Sample ids: 509640, 505484, 504872, 502168, 506783, 509187

**A23 - next_action_date, account_status** (40 rows)

Closed accounts still carrying a future next_action_date, so they stay in collector queues.

Sample ids: 501303, 505548, 509651, 503921, 504402, 503613

**A24 - employer_name, address_line2, middle_initial, phone_work, email** (70 rows)

Empty values written five different ways: blank, NULL, N/A, n/a, -, UNKNOWN, none.

*Anything counting nulls will undercount unless these are normalized first.*

Sample ids: 508205, 508080, 504150, 500886, 503496, 507280

**A25 - state** (6 rows)

Invalid or non-standard state codes.

Sample ids: 507352, 500400, 500969, 507319, 507794, 504284

**A26 - ssn, last_name** (30 rows)

Not a defect: roughly 30 consumers hold multiple accounts across different clients. The set rewards recognizing this before deduplicating.

*Distinguish these from the true duplicates in A15.*

Sample ids: 505641, 503222, 503587, 500441, 504542, 502660

**A27 - total_paid, adjustment_amount** (20 rows)

Settlements accepted for less than the client's contractual min_settlement_pct. The account was closed as SETTLED_IN_FULL and the rest of the balance waived without authority.

*Easiest to see as payment_arrangements.settlement_pct below clients.min_settlement_pct; otherwise compare total_paid against placement_balance + interest + fees.*

Sample ids: 509039, 500956, 506843, 505643, 503721, 504225

**A28 - account_status, client_id** (15 rows)

Accounts closed as SETTLED_IN_FULL under clients whose contract sets allows_settlement = N.

*Join accounts to clients and check account_status against allows_settlement.*

Sample ids: 506636, 509871, 503418, 502335, 501742, 506978

**A29 - status_class, account_status** (30 rows)

status_class disagrees with account_status. Most are closed accounts still classed as OPEN or PTP, so they inflate open inventory and stay in work queues; a few are open accounts classed CLOSED, so they disappear from reporting.

*status_class is a denormalized rollup of account_status. Rebuild it from the status and compare, rather than trusting the stored value.*

Sample ids: 503902, 504980, 505880, 502662, 502573, 503481

### payments

**P1 - account_id** (12 rows)

Payments referencing account_ids that are not in accounts.csv.

Sample ids: 9010151, 9005219, 9008241, 9002139, 9006356, 9003255

**P2 - payment_date** (25 rows)

Payments dated after the account was closed, including payments taken on bankruptcy and deceased accounts.

*Join to accounts.closed_date. Some of these are compliance problems, not just data problems.*

Sample ids: 9011191, 9003215, 9015148, 9004851, 9006764, 9009931

**P3 - payment_amount** (10 rows)

Posted payments with a zero or negative amount.

Sample ids: 9008000, 9005005, 9001741, 9002060, 9008606, 9003214

**P4 - payment_id, transaction_reference** (15 rows)

Duplicate payment rows: identical account, date, amount and transaction reference under two payment_ids.

*Sample values are id pairs. Also inflates total collections if counted naively.*

Sample ids: 9006752/9800000, 9006104/9800001, 9005170/9800002, 9002712/9800003, 9003316/9800004, 9008301/9800005

**P5 - payment_date** (6 rows)

Payment dates in the future.

Sample ids: 9013082, 9014085, 9007901, 9000439, 9011456, 9012493

**P6 - received_by_user_id** (20 rows)

Missing or invalid receiving user on the payment.

Sample ids: 9009448, 9014220, 9007593, 9009506, 9004686, 9010357

**P7 - payment_date, posted_date** (5 rows)

Payments posted before the account was ever placed with the agency.

Sample ids: 9014428, 9014202, 9015963, 9007341, 9002244

**P8 - payment_method** (18 rows)

Payment method spelled several different ways for the same method.

*Grouping by payment_method without normalizing splits the same method across buckets.*

Sample ids: 9008410, 9009322, 9014139, 9001253, 9015626, 9000949

### payment_arrangements

**R1 - arrangement_status, next_payment_date** (60 rows)

Arrangements still marked ACTIVE whose next payment was due months ago; they are broken but nothing reflects it.

*These accounts are also still counted in 'accounts on a plan' reporting.*

Sample ids: 702250, 700850, 700835, 702102, 701483, 702465

**R2 - arrangement_status** (18 rows)

Active arrangements, with a future payment still scheduled, sitting on accounts that are already closed. Several of these accounts are closed as bankruptcy or deceased.

*Join arrangements to accounts.closed_date.*

Sample ids: 700422, 701447, 701354, 700274, 700533, 702234

**R3 - installment_amount, number_of_installments, total_amount** (30 rows)

installment_amount times number_of_installments does not reconcile to total_amount.

Sample ids: 701042, 702076, 700207, 702380, 701099, 700089

**R4 - payments_made, amount_paid_to_date** (12 rows)

Arrangements claiming payments were made when payments.csv has none for that arrangement.

Sample ids: 700916, 702423, 702107, 701478, 700021, 700709

**R5 - account_id, arrangement_status** (10 rows)

Two simultaneously ACTIVE arrangements on the same account.

*Sample values are account_ids. Group by account_id where status = ACTIVE.*

Sample ids: 502961, 509160, 506299, 502907, 506643, 508746

**R6 - arrangement_status, broken_date** (8 rows)

broken_date and broken_reason populated while arrangement_status is still ACTIVE.

Sample ids: 701089, 701332, 702314, 702355, 701570, 700560

### notes

**N1 - user_id** (37 rows)

Notes written by user_id 9999, which does not exist in users.csv.

*Left join notes to users on user_id.*

Sample ids: 501434, 501446, 501499, 501553, 502065, 502510

**N2 - note_datetime** (25 rows)

Notes dated before the account's placement_date.

Sample ids: 500433, 500981, 501061, 501301, 502288, 502407

**N3 - note_datetime** (119 rows)

Outbound call notes timestamped outside 8:00am-9:00pm, an FDCPA calling-window problem.

*Filter contact_type = OUTBOUND_CALL and check the hour part of note_datetime.*

Sample ids: 500210, 500306, 500367, 500499, 500547, 500593

**N4a - note_text** (35 rows)

Notes documenting a cease and desist request where accounts.cease_desist_flag is still N.

*Search note_text for 'cease and desist' and compare the account flag.*

Sample ids: 500100, 500193, 500581, 501211, 502539, 502884

**N4b - note_text** (25 rows)

Notes documenting attorney representation where accounts.attorney_represented_flag is still N.

Sample ids: 500922, 501007, 501850, 502369, 502515, 503593

**N5 - note_text** (49 rows)

Exact duplicate notes: same account, timestamp and text under two note_ids.

Sample ids: 500105, 500198, 500553, 500688, 501055, 501118

**N6 - note_text** (60 rows)

Note text containing embedded newlines, quotes and commas. Correct per RFC 4180 but it breaks naive line-by-line parsing.

*notes.csv has far more physical lines than records.*

Sample ids: 500013, 500152, 500163, 500389, 501072, 501093

**N7 - note_datetime** (30 rows)

Collection calls logged after the account was closed, including bankruptcy and deceased accounts.

Sample ids: 500187, 500273, 500964, 501771, 502578, 502654

**N8 - note_text** (5 rows)

Third-party disclosure: the balance and creditor were revealed to someone other than the consumer.

*A compliance issue rather than a structural one.*

Sample ids: 502225, 503314, 504448, 504617, 504950

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
