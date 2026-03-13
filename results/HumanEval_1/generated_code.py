from typing import List


def separate_paren_groups(paren_string: str) -> List[str]:
    """ Input to this function is a string containing multiple groups of nested parentheses. Your goal is to
    separate those group into separate strings and return the list of those.
    Separate groups are balanced (each open brace is properly closed) and not nested within each other
    Ignore any spaces in the input string.
    >>> separate_paren_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    """

from typing import List


def separate_paren_groups(paren_string: str) -> List[str]:
    result = []
    temp_group = []
    paren_stack = []

    for char in paren_string.replace(" ", ""):
        if char == '(':
            paren_stack.append(char)
            temp_group.append(char)
        elif char == ')' and paren_stack:
            temp_group.append(char)
            paren_stack.pop()
            if not paren_stack:
                result.append(''.join(temp_group))
                temp_group = []

    return result
