from generated_code import has_close_elements

from typing import List

def test_has_close_elements_empty_list():
    assert has_close_elements([], 0.5) == False

def test_has_close_elements_single_element():
    assert has_close_elements([1.0], 0.5) == False

def test_has_close_elements_two_elements_no_close():
    assert has_close_elements([1.0, 2.0], 0.3) == False

def test_has_close_elements_two_elements_close():
    assert has_close_elements([1.0, 1.3], 0.3) == True

def test_has_close_elements_multiple_elements_with_close_pair():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True