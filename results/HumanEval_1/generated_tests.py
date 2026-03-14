from typing import List
from generated_code import separate_paren_groups

def test_normal_case():
    assert separate_paren_groups('( ) (( )) (( )( ))') == ['()', '(())', '(()())']

def test_single_group():
    assert separate_paren_groups('()') == ['()']

def test_multiple_empty_groups():
    assert separate_paren_groups('((()))(())()') == ['((()))', '(())', '()']

def test_nested_groups():
    assert separate_paren_groups('((( ))) (( )) ()') == ['(((( )))', '(( ))', '()']

def test_single_open_group():
    assert separate_paren_groups('(') == ['(']