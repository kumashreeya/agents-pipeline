from generated_code import separate_paren_groups

from typing import List


def test_empty_input():
    assert separate_paren_groups("") == [], "Empty input should return an empty list"

def test_single_group():
    assert separate_paren_groups("()") == ["()"], "Single group should be returned as is"

def test_multiple_groups():
    assert separate_paren_groups("( ) (( )) (( )( ))") == ['()', '(())', '(()())'], "Multiple groups should be separated correctly"

def test_nested_groups():
    assert separate_paren_groups("((()))") == ["((()))"], "Nested groups should not be separated"

def test_spaces_ignored():
    assert separate_paren_groups("( ) (( ))  (( )( ))") == ['()', '(())', '(()())'], "Spaces in the input string should be ignored"