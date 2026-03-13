from generated_code import separate_paren_groups


def test_separate_paren_groups_empty_input():
    assert separate_paren_groups("") == []


def test_separate_paren_groups_single_group():
    assert separate_paren_groups("( )") == ["()"]


def test_separate_paren_groups_multiple_non_nested_groups():
    assert separate_paren_groups("(( )) (( )( ))") == ["(()())", "(())"]


def test_separate_paren_groups_nested_groups():
    assert separate_paren_groups("((()))") == ["((()))"]


def test_separate_paren_groups_mixed_spaces():
    assert separate_paren_groups("( )  (( )) (( )( ))") == ['()', '(())', '(()())']