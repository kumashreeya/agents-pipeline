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


    def separate_parentheses_groups(paren_string: str) -> List[str]:
    """ Extracts and returns separate groups of balanced parentheses from the input string.

    The function ignores spaces in the input and ensures that each group is balanced (each open parenthesis is closed).
    >>> separate_parentheses_groups('( ) (( )) (( )( ))')
    ['()', '(())', '(()())']
    """
    def extract_group(string: str) -> str:
        stack = []
        result = []
        for char in string:
            if char == '(':
                stack.append(char)
            elif char == ')':
                stack.pop()
                result.append(char)
            if not stack:
                return ''.join(result)

    paren_string = paren_string.replace(" ", "")
    groups = []

    current_index = 0
    while current_index < len(paren_string):
        group = extract_group(paren_string[current_index:])
        if group:
            groups.append(group)
            current_index += len(group) - 1

    return groups


    # Lint fixes and improved variable names for better readability
