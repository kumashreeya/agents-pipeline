from generated_code import has_close_elements

from typing import List


def test_has_close_elements_normal():
    assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False

def test_has_close_elements_edge_empty():
    assert has_close_elements([], 0.5) == False

def test_has_close_elements_boundary_single():
    assert has_close_elements([42.0], 0.5) == False

def test_has_close_elements_normal_positive_threshold():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True

def test_has_close_elements_edge_closest_elements_same_threshold():
    assert has_close_elements([1.0, 1.9, 2.0], 0.1) == True