from generated_code import below_zero

from typing import List


def test_below_zero_normal():
    assert not below_zero([1, 2, 3])

def test_below_zero_with_negative_deposit():
    assert below_zero([1, 2, -4, 5])

def test_below_zero_all_negative():
    assert below_zero([-1, -2, -3])

def test_below_zero_empty_list():
    assert not below_zero([])

def test_below_zero_single_operation():
    assert not below_zero([0])