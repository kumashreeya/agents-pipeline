from generated_code import below_zero

def test_below_zero_normal():
    assert below_zero([1, 2, 3]) == False

def test_below_zero_edge_negative_deposit():
    assert below_zero([-1, 2, 3]) == True

def test_below_zero_boundary_positive_deposit():
    assert below_zero([10, 2, 3]) == False

def test_below_zero_negative_withdrawal():
    assert below_zero([1, -2, 3]) == True

def test_below_zero_empty_operations():
    assert below_zero([]) == False