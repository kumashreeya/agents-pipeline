from typing import List


def below_zero(operations: List[int]) -> bool:
    """ You're given a list of deposit and withdrawal operations on a bank account that starts with
    zero balance. Your task is to detect if at any point the balance of account fallls below zero, and
    at that point function should return True. Otherwise it should return False.
    >>> below_zero([1, 2, 3])
    False
    >>> below_zero([1, 2, -4, 5])
    True
    """


# FEEDBACK FROM PREVIOUS ATTEMPT:
# Refactor the function to reduce cyclomatic complexity. For example, you could use a while loop instead of a for loop.
    balance = 0
    for operation in operations:
        balance += operation
        if balance < 0:
            return True
    return False
