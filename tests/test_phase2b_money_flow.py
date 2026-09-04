from revenex.phase2b_money_flow import analyze_money_flow


def test_money_flow_calculates_net_cash():
    result = analyze_money_flow(
        {
            "invoice_amount": 500000,
            "collected_amount": 420000,
            "settled_amount": 405000,
            "fees": 5000,
            "tax": 1000,
        }
    )

    assert result.invoice_amount == 500000
    assert result.collected_amount == 420000
    assert result.settled_amount == 405000
    assert result.net_cash == 399000
    assert result.outstanding == 80000


def test_money_flow_exposes_unexplained_variance():
    result = analyze_money_flow(
        {
            "invoice_amount": 100000,
            "collected_amount": 100000,
            "settled_amount": 90000,
            "fees": 2000,
            "tax": 1000,
        }
    )

    assert result.unexplained_variance == 10000
    assert result.human_review_required is True


def test_money_flow_normal_case_needs_no_review():
    result = analyze_money_flow(
        {
            "invoice_amount": 100000,
            "collected_amount": 100000,
            "settled_amount": 100000,
            "fees": 2000,
            "tax": 1000,
        }
    )

    assert result.net_cash == 97000
    assert result.unexplained_variance == 0
    assert result.human_review_required is False


def test_money_flow_is_strictly_read_only():
    result = analyze_money_flow(
        {
            "invoice_amount": 500000,
            "collected_amount": 400000,
        }
    )

    assert result.read_only is True
    assert result.execution_allowed is False
    assert result.financial_mutation is False
    assert result.provider_mutation is False


def test_invalid_values_are_safe():
    result = analyze_money_flow(
        {
            "invoice_amount": "invalid",
            "collected_amount": None,
            "fees": "bad",
            "tax": "bad",
        }
    )

    assert result.invoice_amount == 0
    assert result.collected_amount == 0
    assert result.net_cash == 0
    assert result.read_only is True
