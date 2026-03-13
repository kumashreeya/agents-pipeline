from generated_code import mean_absolute_deviation


def test_mean_absolute_deviation_normal():
    assert mean_absolute_deviation([1.0, 2.0, 3.0, 4.0]) == 1.0

def test_mean_absolute_deviation_single_element():
    assert mean_absolute_deviation([5.0]) == 0.0

def test_mean_absolute_deviation_negative_numbers():
    assert mean_absolute_deviation([-1.0, -2.0, -3.0, -4.0]) == 1.0

def test_mean_absolute_deviation_edge_case():
    assert mean_absolute_deviation([0.0, 0.0, 0.0, 0.0]) == 0.0

def test_mean_absolute_deviation_empty_input():
    assert mean_absolute_deviation([]) == 0.0