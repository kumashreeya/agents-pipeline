from generated_code import truncate_number

def test_truncate_number_normal_cases():
    assert truncate_number(3.5) == 0.5
    assert truncate_number(10.99) == 0.99
    assert truncate_number(7.0) == 0.0

def test_truncate_number_edge_case():
    assert truncate_number(2.0) == 0.0
    assert truncate_number(4.9) == 0.9

def test_truncate_number_boundary_cases():
    assert truncate_number(5.0) == 0.0
    assert truncate_number(100.0) == 0.0

def test_truncate_number_empty_input():
    with pytest.raises(TypeError):
        truncate_number(None)

def test_truncate_number_non_float_input():
    with pytest.raises(TypeError):
        truncate_number("abc")