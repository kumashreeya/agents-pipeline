from generated_code import has_close_elements

from typing import List


# Test functions
def test_has_close_elements_normal_case():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True

def test_has_close_elements_same_numbers():
    assert has_close_elements([1.0, 1.0, 1.0], 0.1) == False

def test_has_close_elements_single_number():
    assert has_close_elements([5.0], 1.0) == False

def test_has_close_elements_empty_list():
    assert has_close_elements([], 0.1) == False

def test_has_close_elements_same_element_negative_threshold():
    assert has_close_elements([-1.0, -2.8, -3.0], -0.5) == False