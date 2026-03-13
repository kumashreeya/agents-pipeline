from generated_code import below_zero

from typing import List


# FEEDBACK FROM PREVIOUS ATTEMPT:
# Refactor the `below_zero` function to reduce its cyclomatic complexity. Consider using a loop instead of recursion or simplifying conditional logic.
def test_below_zero_normal():
    assert below_zero([1, 2, 3]) == False

def test_below_zero_negative_operation():
    assert below_zero([1, -4, 5]) == True

def test_below_zero_multiple_negatives():
    assert below_zero([-2, -3, -1]) == True

def test_below_zero_edge_case_single_negative():
    assert below_zero([-10]) == True

def test_below_zero_empty_operations():
    assert below_zero([]) == False