from generated_code import truncate_number

def test_truncate_number_normal():
    assert truncate_number(3.5) == 0.5

def test_truncate_number_integer():
    assert truncate_number(10.0) == 0.0

def test_truncate_number_zero():
    assert truncate_number(0.0) == 0.0

def test_truncate_number_negative():
    with pytest.raises(ValueError):
        truncate_number(-3.5)

def test_truncate_number_boundary():
    assert truncate_number(2.9999999999) == 0.01