from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """


# FEEDBACK FROM PREVIOUS ATTEMPT:
# Refactor the code to reduce cyclomatic complexity by using a more efficient algorithm, such as sorting and checking adjacent elements. Also, consider improving the maintainability by adding comments and documentation.
    numbers.sort()
    for i in range(len(numbers) - 1):
        if numbers[i + 1] - numbers[i] < threshold:
            return True
    return False
