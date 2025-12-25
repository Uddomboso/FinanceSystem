import pytest

def test_commitment_delta_exactness():
    """Adding a $1 commitment changes balances by exactly $1, regardless of base balance."""
    base_balances = [0, 100, -100, 0.01, 100000, -104893.12]
    for base in base_balances:
        commitments = 0
        new_commitment = 1.0
        # core logic, no clamping
        price_before = base - commitments
        price_after = base - (commitments + new_commitment)
        delta = price_after - price_before
        assert abs(delta) == pytest.approx(-1.0, abs=1e-9), f"Failed for base={base}: delta={delta}"
