from generated_code import mean_absolute_deviation

from typing import List


def test_mean_absolute_deviation_empty_list():
    assert mean_absolute_deviation([]) == 0.0


def test_mean_absolute_deviation_single_element():
    assert mean_absolute_deviation([5.0]) == 0.0


def test_mean_absolute_deviation_positive_numbers():
    numbers = [1.0, 2.0, 3.0, 4.0]
    expected_mad = (abs(1 - 2.5) + abs(2 - 2.5) + abs(3 - 2.5) + abs(4 - 2.5)) / 4
    assert mean_absolute_deviation(numbers) == expected_mad


def test_mean_absolute_deviation_negative_numbers():
    numbers = [-1.0, -2.0, -3.0, -4.0]
    expected_mad = (abs(-1 + 1.5) + abs(-2 + 1.5) + abs(-3 + 1.5) + abs(-4 + 1.5)) / 4
    assert mean_absolute_deviation(numbers) == expected_mad


def test_mean_absolute_deviation_positive_and_negative_numbers():
    numbers = [1.0, -2.0, 3.0, -4.0]
    expected_mad = (abs(1 + 1.5) + abs(-2 + 1.5) + abs(3 + 1.5) + abs(-4 + 1.5)) / 4
    assert mean_absolute_deviation(numbers) == expected_mad