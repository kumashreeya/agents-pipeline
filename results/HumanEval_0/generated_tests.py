from generated_code import has_close_elements
from typing import List


def test_normal_case():
    assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False

def test_edge_case():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True

def test_single_element_list():
    assert has_close_elements([1.0], 0.5) == False

def test_negative_numbers():
    assert has_close_elements([-1.0, -2.0, -3.0], 0.5) == False
    assert has_close_elements([-1.0, -2.8, -3.0, -4.0, -5.0, -2.0], 0.3) == True

def test_zero_threshold():
    assert has_close_elements([1.0, 2.0, 3.0], 0.0) == False