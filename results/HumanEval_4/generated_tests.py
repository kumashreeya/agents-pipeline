from generated_code import mean_absolute_deviation

def test_normal_case():
    assert mean_absolute_deviation([1.0, 2.0, 3.0, 4.0]) == 1.0

def test_single_element():
    assert mean_absolute_deviation([5.0]) == 0.0

def test_negative_numbers():
    assert mean_absolute_deviation([-1.0, -2.0, -3.0, -4.0]) == 1.0

def test_zero_mean():
    assert mean_absolute_deviation([0.0, 0.0, 0.0, 0.0]) == 0.0

def test_large_numbers():
    assert mean_absolute_deviation([1000.0, 2000.0, 3000.0, 4000.0]) == 1500.0