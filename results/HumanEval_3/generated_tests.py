from generated_code import below_zero

from typing import List


def test_below_zero_normal():
    assert not below_zero([1, 2, 3])

def test_below_zero_withdrawal():
    assert below_zero([1, 2, -4, 5])

def test_below_zero_only_negative_operations():
    assert below_zero([-1, -2, -3])

def test_below_zero_multiple_negative_operations():
    assert below_zero([10, -5, -15])

def test_below_zero_single_negative_operation():
    assert below_zero([-1])