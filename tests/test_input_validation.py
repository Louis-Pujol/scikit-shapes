"""Tests for the input validation decorators."""

import pytest
from beartype.roar import BeartypeCallHintParamViolation
from jaxtyping import TypeCheckError
import skshapes as sks


@sks.one_and_only_one(["a", "b"])
@sks.typecheck
def func_one_and_only_one(a: int = None, b: int = None):
    """An example function with one_and_only_one."""
    pass


def test_one_and_only_one_decorator(func=func_one_and_only_one):
    """Test the one_and_only_one decorator.

    This test checks that the one_and_only_one decorator raises an error
    when the function is called with more than one of the arguments
    specified in the decorator or when none of the arguments is specified.

    """
    func(a=1)  # ok
    func(b=1)  # ok
    with pytest.raises(ValueError):
        func(2)  # not ok (must be passed as keyword)
    with pytest.raises(ValueError):
        func(a=1, b=1)  # not ok (both arguments are specified)
    with pytest.raises(ValueError):
        func()  # not ok (no argument is specified)
    with pytest.raises(TypeCheckError):
        func(a="dog")  # not ok : wrong type


@sks.no_more_than_one(["a", "b"])
@sks.typecheck
def func_no_more_than_one(*, a: int = None, b: int = None):
    """An example function with no_more_than_one."""
    pass


def test_no_more_than_one(func=func_no_more_than_one):
    """Test the no_more_than_one decorator.

    This test checks that the no_more_than_one decorator raises an error
    when the function is called with more than one of the arguments
    specified in the decorator.

    """
    func(a=1)  # ok
    func(b=1)  # ok
    func()  # ok
    with pytest.raises(TypeError):
        func(2)
    with pytest.raises(ValueError):
        func(a=1, b=1)  # not ok (both arguments are specified)
    with pytest.raises(TypeCheckError):
        func(a="dog")  # not ok : wrong type
