from generated_code import truncate_number

def test_normal_case():
    assert truncate_number(3.5) == 0.5

def test_zero_decimal():
    assert truncate_number(2.0) == 0.0

def test_negative_input():
    assert truncate_number(-1.7) == -0.7

def test_integer_input():
    assert truncate_number(4.0) == 0.0

def test_large_number():
    assert truncate_number(987654321.123456789) == 0.123456789