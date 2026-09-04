# REVENEX — Phase 2: Understand

## Objective

Explain why observed revenue is at risk.

## Inputs

Phase 1 observation signals:

- Revenue at risk
- Failed payments
- Overdue invoices
- At-risk customers
- Other structured risk signals supplied by analysis

## Outputs

- Top supported risk reason
- Observed risk reasons
- Supporting evidence
- Risk explanation

## Principle

REVENEX must explain only what the available data supports.

Missing information is represented as:

- `—`
- `Insufficient data`

## Boundary

Phase 2 does NOT:

- predict recovery probability
- estimate future recovery
- select recovery actions
- contact customers
- create payment links
- move money
- mutate Razorpay state
- autonomously execute recovery

## Pipeline Position

Foundation
→ Observe
→ **Understand**
→ Predict
→ Simulate
→ Decide
→ Act
→ Monitor Outcome
→ Learn
→ Audit
→ Autonomous Revenue OS
