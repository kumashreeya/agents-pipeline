from generated_code import has_close_elements

from typing import List


def test_has_close_elements_empty_list():
    assert not has_close_elements([], 0.5)

def test_has_close_elements_single_element():
    assert not has_close_elements([1.0], 0.5)

def test_has_close_elements_no_close_elements():
    assert not has_close_elements([1.0, 2.0, 3.0], 0.5)

def test_has_close_elements_edge_case():
    assert has_close_elements([1.0, 2.0, 3.0], 0.499)

def test_has_close_elements_two_close_elements():
    assert has_close_elements([1.0, 1.01, 3.0], 0.01)