# REVENEX — Phase 16 Cross-System Correlation Intelligence

## Purpose

Phase 16 connects financial signals that normally exist in
separate operational systems.

The analysis follows:

Invoice
→ Payment
→ Settlement
→ Payout

This allows REVENEX to identify gaps that may not be obvious
when each system is inspected independently.

## Signals

The engine can identify:

- Collection gaps
- Settlement gaps
- Payout gaps
- Multiple simultaneous gaps
- Fully aligned records

## Correlation Score

The score represents the proportion of invoice exposure
represented by the observed cross-system gaps.

The score is deterministic and bounded between 0 and 1.

## Severity

Signals are classified as:

- CRITICAL
- HIGH
- MEDIUM
- LOW

## Evidence

Every correlation signal contains references to:

- Entity
- Invoice amount
- Payment amount
- Settlement amount
- Payout amount

## Executive Question

Phase 15 asked:

"Where is the recoverable opportunity?"

Phase 16 adds:

"Do the different revenue systems agree with each other?"

This is important because a revenue problem may be hidden
between system boundaries.

## Safety

Phase 16 is read-only intelligence.

execution_allowed = False

automatic_action = False

financial_mutation = False

provider_mutation = False

read_only = True

human_review_required = True

No settlement, payout, payment, invoice, or provider action
is automatically performed.
