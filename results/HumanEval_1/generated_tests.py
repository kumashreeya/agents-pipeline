from generated_code import separate_paren_groups

from typing import List

def test_separate_paren_groups_normal():
    assert separate_paren_groups('( ) (( )) (( )( ))') == ['()', '(())', '(()())']

def test_separate_paren_groups_single():
    assert separate_paren_groups('(') == ['()']

def test_separate_paren_groups_empty():
    assert separate_paren_groups('') == []

def test_separate_paren_groups_nested():
    assert separate_paren_groups('((()))(())') == ['((()))', '(())']

def test_separate_paren_groups_spaces():
    assert separate_paren_groups('( ) (( )) (( )( ))') == ['()', '(())', '(()())']