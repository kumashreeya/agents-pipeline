from generated_code import truncate_number

def test_truncate_number_positive():
    assert truncate_number(3.5) == 0.5, "Test case for positive number failed"
    
def test_truncate_number_edge():
    assert truncate_number(2.99999) == 0.99999, "Test case for edge case failed"

def test_truncate_number_boundary():
    assert truncate_number(4.0) == 0.0, "Test case for boundary condition failed"
    
def test_truncate_number_zero():
    assert truncate_number(0.0) == 0.0, "Test case for zero number failed"
    
def test_truncate_number_negative():
    with pytest.raises(ValueError):
        truncate_number(-1.5), "Test case for negative number failed"