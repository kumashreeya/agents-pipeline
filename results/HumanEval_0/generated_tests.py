from generated_code import has_close_elements

from typing import List


def test_has_close_elements_normal():
    assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False

def test_has_close_elements_edge():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True
    assert has_close_elements([1.0, 2.79, 3.0, 4.0, 5.0, 2.0], 0.3) == False

def test_has_close_elements_boundary():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.0) == True
    assert has_close_elements([1.0, 2.79, 3.0, 4.0, 5.0, 2.0], 1.0) == False

def test_has_close_elements_empty():
    assert has_close_elements([], 0.5) == False

def test_has_close_elements_single_element():
    assert has_close_elements([1.0], 0.5) == False