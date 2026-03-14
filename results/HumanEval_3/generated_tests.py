from generated_code import below_zero

def test_normal_case():
    assert below_zero([1, 2, 3]) == False

def test_single_negative_operation():
    assert below_zero([-5]) == True

def test_multiple_operations_with_positive_balance():
    assert below_zero([10, 20, 30]) == False

def test_multiple_operations_with_negative_balance():
    assert below_zero([10, -20, 30]) == True

def test_single_operation_with_negative_balance():
    assert below_zero([-10]) == True