from generated_code import has_close_elements


def test_has_close_elements_no_closeness():
    assert not has_close_elements([1.0, 2.0, 3.0], 0.5)


def test_has_close_elements_single_pair_closeness():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)


def test_has_close_elements_multiple_pairs_closeness():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.6, 2.4], 0.2)


def test_has_close_elements_edge_case_threshold_one():
    assert not has_close_elements([1.0, 1.1, 1.2, 1.3], 1.0)


def test_has_close_elements_empty_list():
    assert not has_close_elements([], 0.5)