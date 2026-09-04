from revenex.prediction.revenue_predictor import (
    predict_all_customers,
    predict_customer_revenue,
)


def test_prediction_returns_customer_probability_and_risk():
    prediction = predict_customer_revenue(
        "customer-1",
        [
            {
                "customer_id": "customer-1",
                "amount": 100000,
                "outstanding_amount": 50000,
                "days_overdue": 60,
            }
        ],
        [
            {
                "customer_id": "customer-1",
                "amount": 50000,
            }
        ],
    )

    assert prediction.customer_id == "customer-1"
    assert 0.0 <= prediction.payment_probability <= 1.0
    assert 0.0 <= prediction.late_payment_risk <= 1.0
    assert prediction.expected_collection >= 0
    assert prediction.revenue_at_risk >= 0
    assert 0.0 <= prediction.confidence <= 1.0


def test_prediction_detects_revenue_at_risk():
    prediction = predict_customer_revenue(
        "customer-1",
        [
            {
                "customer_id": "customer-1",
                "amount": 200000,
                "outstanding_amount": 180000,
                "days_overdue": 90,
            }
        ],
        [],
    )

    assert prediction.late_payment_risk > 0.50
    assert prediction.revenue_at_risk > 0
    assert prediction.expected_collection < 180000


def test_prediction_handles_customer_without_revenue():
    prediction = predict_customer_revenue(
        "customer-1",
        [],
        [],
    )

    assert prediction.payment_probability == 0.0
    assert prediction.expected_collection == 0.0
    assert prediction.revenue_at_risk == 0.0
    assert prediction.confidence == 0.0


def test_predictions_cover_all_customers():
    predictions = predict_all_customers(
        [
            {
                "customer_id": "customer-a",
                "amount": 10000,
                "outstanding_amount": 2000,
            },
            {
                "customer_id": "customer-b",
                "amount": 20000,
                "outstanding_amount": 5000,
            },
        ],
        [],
    )

    assert len(predictions) == 2
    assert {
        prediction.customer_id
        for prediction in predictions
    } == {"customer-a", "customer-b"}


def test_prediction_is_read_only():
    invoices = [
        {
            "customer_id": "customer-1",
            "amount": 100000,
            "outstanding_amount": 50000,
            "days_overdue": 45,
        }
    ]

    payments = [
        {
            "customer_id": "customer-1",
            "amount": 50000,
        }
    ]

    invoices_before = [dict(item) for item in invoices]
    payments_before = [dict(item) for item in payments]

    predict_customer_revenue(
        "customer-1",
        invoices,
        payments,
    )

    assert invoices == invoices_before
    assert payments == payments_before
