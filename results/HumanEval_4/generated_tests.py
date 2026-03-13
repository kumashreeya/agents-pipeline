from generated_code import mean_absolute_deviation

from typing import List


def test_mean_absolute_deviation_normal_input():
    assert mean_absolute_deviation([1.0, 2.0, 3.0, 4.0]) == 1.0

def test_mean_absolute_deviation_single_element():
    assert mean_absolute_deviation([5.5]) == 0.0

def test_mean_absolute_deviation_empty_list():
    assert mean_absolute_deviation([]) == 0.0

def test_mean_absolute_deviation_large_numbers():
    assert mean_absolute_deviation([100, 200, 300, 400]) == 150.0

def test_mean_absolute_deviation_decimal_numbers():
    assert abs(mean_absolute_deviation([1.1, 2.2, 3.3, 4.4]) - 1.25) < 1e-9