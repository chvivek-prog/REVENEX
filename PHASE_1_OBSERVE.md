# REVENEX — Phase 1: Observe

## Objective

Observe available revenue data and identify measurable revenue at risk.

## Observation Signals

- Revenue at risk
- At-risk customers
- Failed payments
- Overdue invoices
- Other explicitly available risk signals

## Principle

Only data supported by the existing analysis payload is displayed.

Missing information is represented as `—` or `Insufficient data`.

## Boundary

Phase 1 does NOT:

- predict recovery
- select recovery actions
- contact customers
- create payment links
- move money
- mutate Razorpay state
- autonomously execute recovery

## Pipeline Position

Foundation
→ **Observe**
→ Understand
→ Predict
→ Simulate
→ Decide
→ Act
→ Monitor Outcome
→ Learn
→ Audit
→ Autonomous Revenue OS
