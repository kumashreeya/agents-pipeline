from generated_code import truncate_number

def test_truncate_number_normal():
    assert truncate_number(3.5) == 0.5, "Test for 3.5 failed"

def test_truncate_number_edge():
    assert truncate_number(2.9999) == 0.9999, "Test for 2.9999 failed"

def test_truncate_number_boundary():
    assert truncate_number(4.0) == 0.0, "Test for 4.0 failed"

def test_truncate_number_empty_input():
    try:
        truncate_number(None)
    except TypeError as e:
        assert str(e) == "truncate_number() takes exactly one argument (1 given)", "Test for empty input failed"