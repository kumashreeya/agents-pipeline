from generated_code_clean import has_close_elements

def test_normal():
    assert has_close_elements([1.0, 2.0, 3.0], 0.5) == False

def test_close():
    assert has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3) == True

def test_empty():
    assert has_close_elements([], 0.5) == False

def test_single():
    assert has_close_elements([1.0], 0.5) == False
