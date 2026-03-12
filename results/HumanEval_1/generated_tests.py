from generated_code import separate_paren_groups

def test_empty_input():
    assert separate_paren_groups("") == []

def test_single_group():
    assert separate_paren_groups("()") == ["()"]

def test_multiple_non_nested_groups():
    assert separate_paren_groups("( ) (( )) (( )( ))") == ['()', '(())', '(()())']

def test_nested_groups():
    assert separate_paren_groups("((())) (()) (()(()))") == ['((()))', '(())', '(()(()))']

def test_mixed_content():
    assert separate_paren_groups("Hello (world) how are you doing today? ((greatly))!") == ['(world)', '((greatly))!']