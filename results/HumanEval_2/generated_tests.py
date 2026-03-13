from generated_code import truncate_number

def test_truncate_number_normal():
    assert truncate_number(3.5) == 0.5

def test_truncate_number_positive_integer():
    assert truncate_number(4.0) == 0.0

def test_truncate_number_negative_decimal():
    assert truncate_number(-2.7) == -0.7

def test_truncate_number_zero():
    assert truncate_number(0.0) == 0.0

def test_truncate_number_max_value():
    assert truncate_number(float('inf')) == float('-inf')