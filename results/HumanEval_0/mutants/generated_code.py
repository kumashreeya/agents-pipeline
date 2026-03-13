from typing import List
from typing import Annotated
from typing import Callable
from typing import ClassVar

MutantDict = Annotated[dict[str, Callable], "Mutant"] # type: ignore


def _mutmut_trampoline(orig, mutants, call_args, call_kwargs, self_arg = None): # type: ignore
    """Forward call to original or mutated function, depending on the environment"""
    import os # type: ignore
    mutant_under_test = os.environ['MUTANT_UNDER_TEST'] # type: ignore
    if mutant_under_test == 'fail': # type: ignore
        from mutmut.__main__ import MutmutProgrammaticFailException # type: ignore
        raise MutmutProgrammaticFailException('Failed programmatically')       # type: ignore
    elif mutant_under_test == 'stats': # type: ignore
        from mutmut.__main__ import record_trampoline_hit # type: ignore
        record_trampoline_hit(orig.__module__ + '.' + orig.__name__) # type: ignore
        # (for class methods, orig is bound and thus does not need the explicit self argument)
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    prefix = orig.__module__ + '.' + orig.__name__ + '__mutmut_' # type: ignore
    if not mutant_under_test.startswith(prefix): # type: ignore
        result = orig(*call_args, **call_kwargs) # type: ignore
        return result # type: ignore
    mutant_name = mutant_under_test.rpartition('.')[-1] # type: ignore
    if self_arg is not None: # type: ignore
        # call to a class method where self is not bound
        result = mutants[mutant_name](self_arg, *call_args, **call_kwargs) # type: ignore
    else:
        result = mutants[mutant_name](*call_args, **call_kwargs) # type: ignore
    return result # type: ignore


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    """ Check if in given list of numbers, are any two numbers closer to each other than
    given threshold.
    >>> has_close_elements([1.0, 2.0, 3.0], 0.5)
    False
    >>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)
    True
    """



from typing import List


def has_close_elements(numbers: List[float], threshold: float) -> bool:
    args = [numbers, threshold]# type: ignore
    kwargs = {}# type: ignore
    return _mutmut_trampoline(x_has_close_elements__mutmut_orig, x_has_close_elements__mutmut_mutants, args, kwargs, None)


def x_has_close_elements__mutmut_orig(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(numbers[i] - numbers[i + 1]) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_1(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(None):
        if abs(numbers[i] - numbers[i + 1]) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_2(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) + 1):
        if abs(numbers[i] - numbers[i + 1]) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_3(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 2):
        if abs(numbers[i] - numbers[i + 1]) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_4(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(None) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_5(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(numbers[i] + numbers[i + 1]) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_6(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(numbers[i] - numbers[i - 1]) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_7(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(numbers[i] - numbers[i + 2]) < threshold:
            return True
    return False


def x_has_close_elements__mutmut_8(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(numbers[i] - numbers[i + 1]) <= threshold:
            return True
    return False


def x_has_close_elements__mutmut_9(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(numbers[i] - numbers[i + 1]) < threshold:
            return False
    return False


def x_has_close_elements__mutmut_10(numbers: List[float], threshold: float) -> bool:
    numbers.sort()
    for i in range(len(numbers) - 1):
        if abs(numbers[i] - numbers[i + 1]) < threshold:
            return True
    return True

x_has_close_elements__mutmut_mutants : ClassVar[MutantDict] = { # type: ignore
'x_has_close_elements__mutmut_1': x_has_close_elements__mutmut_1, 
    'x_has_close_elements__mutmut_2': x_has_close_elements__mutmut_2, 
    'x_has_close_elements__mutmut_3': x_has_close_elements__mutmut_3, 
    'x_has_close_elements__mutmut_4': x_has_close_elements__mutmut_4, 
    'x_has_close_elements__mutmut_5': x_has_close_elements__mutmut_5, 
    'x_has_close_elements__mutmut_6': x_has_close_elements__mutmut_6, 
    'x_has_close_elements__mutmut_7': x_has_close_elements__mutmut_7, 
    'x_has_close_elements__mutmut_8': x_has_close_elements__mutmut_8, 
    'x_has_close_elements__mutmut_9': x_has_close_elements__mutmut_9, 
    'x_has_close_elements__mutmut_10': x_has_close_elements__mutmut_10
}
x_has_close_elements__mutmut_orig.__name__ = 'x_has_close_elements'

