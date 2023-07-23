from __future__ import annotations

from ..types import typecheck

# from .polydata import PolyData
# import pyvista


# @typecheck
# def read(filename: str) -> PolyData:
#     mesh = pyvista.read(filename)
#     if type(mesh) == pyvista.PolyData:
#         return PolyData.from_pyvista(mesh)
#     else:
#         raise NotImplementedError("Images are not supported yet")


from ..types import (
    Any,
    Optional,
    Union,
    FloatTensor,
    IntTensor,
    Dict,
    NumericalTensor,
    NumericalArray,
    float_dtype,
    FloatArray,
    IntArray,
    int_dtype,
)
import torch
import pyvista
import numpy as np


class DataAttributes(dict):
    """This class is a dictionary aimed to store attributes associated to a data structure (e.g. a set of points, a set of triangles, etc.)
    When a new attribute is added to the dictionary, it is checked that its size is compatible with the size of the data structure.

    The DataAttributes structure ensures that all the attributes are torch.Tensor and on the same device, doing the necessary conversions if needed.


    There are two ways to add an attribute to the dictionary:
        - With an explicit name, using the __setitem__ method (e.g. A["attribute"] = attribute)
        - Without an explicit name, using the append method (e.g. A.append(attribute)) which will automatically set "attribute_{i}" where i is the minimum integer such that "attribute_{i}" is not already in the dictionary

    Args:
        n (int): The number of elements of the set
        device (torch.device): The device on which the attributes should be stored
    """

    @typecheck
    def __init__(self, *, n: int, device: Union[str, torch.device]) -> None:
        self._n = n
        self._device = device

    @typecheck
    def __getitem__(self, key: Any) -> NumericalTensor:
        return dict.__getitem__(self, key)

    @typecheck
    def _check_value(
        self, value: Union[NumericalArray, NumericalTensor]
    ) -> NumericalTensor:
        if isinstance(value, IntArray):
            value = torch.from_numpy(value).to(int_dtype)
        elif isinstance(value, FloatArray):
            value = torch.from_numpy(value).to(float_dtype)

        assert (
            value.shape[0] == self._n
        ), f"Last dimension of the tensor should be {self._n}"
        if value.device != self._device:
            value = value.to(self._device)

        return value

    @typecheck
    def __setitem__(
        self, key: Any, value: Union[NumericalTensor, NumericalArray]
    ) -> None:
        value = self._check_value(value)
        dict.__setitem__(self, key, value)

    @typecheck
    def append(self, value: Union[FloatTensor, IntTensor]) -> None:
        value = self._check_value(value)
        i = 0
        while f"attribute_{i}" in self.keys():
            i += 1

        dict.__setitem__(self, f"attribute_{i}", value)

    @typecheck
    def clone(self) -> DataAttributes:
        clone = DataAttributes(n=self._n, device=self._device)
        for key, value in self.items():
            clone[key] = value.clone()
        return clone

    @typecheck
    def to(self, device: Union[str, torch.device]) -> DataAttributes:
        clone = DataAttributes(n=self._n, device=device)
        for key, value in self.items():
            clone[key] = value.to(device)
        return clone

    @typecheck
    @classmethod
    def from_dict(
        cls,
        attributes: Dict[Any, Union[NumericalTensor, NumericalArray]],
        device: Optional[Union[str, torch.device]] = None,
    ) -> DataAttributes:
        """Create a DataAttributes object from a dictionary of attributes

        Args:
            attributes (Dict[str, Union[FloatTensor, IntTensor]]): The dictionary of attributes

        Returns:
            DataAttributes: The DataAttributes object
        """
        if len(attributes) == 0:
            raise ValueError(
                "The dictionary of attributes should not be empty to initialize a DataAttributes object"
            )

        # Ensure that the number of elements of the attributes is the same
        n = list(attributes.values())[0].shape[0]
        for value in attributes.values():
            assert (
                value.shape[0] == n
            ), "The number of elements of the dictionnary should be the same to be converted into a DataAttributes object"

        if device is None:
            # Ensure that the attributes are on the same device (if they are torch.Tensor, unless they have no device attribute and we set device to cpu)
            if hasattr(list(attributes.values())[0], "device"):
                device = list(attributes.values())[0].device
                for value in attributes.values():
                    assert (
                        value.device == device
                    ), "The attributes should be on the same device to be converted into a DataAttributes object"
            else:
                device = torch.device("cpu")

        output = cls(n=n, device=device)
        for key, value in attributes.items():
            output[key] = value

        return output

    @classmethod
    def from_pyvista_datasetattributes(
        cls,
        attributes: pyvista.DataSetAttributes,
        device: Optional[Union[str, torch.device]] = None,
    ) -> DataAttributes:
        """Create a DataAttributes object from a pyvista.DataSetAttributes object

        Args:
            attributes (pyvista.DataSetAttributes): The pyvista.DataSetAttributes object

        Returns:
            DataAttributes: The DataAttributes object
        """
        # First, convert the pyvista.DataSetAttributes object to a dictionary
        dict_attributes = {}

        for key in attributes.keys():
            if isinstance(attributes[key], np.ndarray):
                dict_attributes[key] = np.array(attributes[key])
            else:
                dict_attributes[key] = np.array(pyvista.wrap(attributes[key]))

        # return attributes

        # Then, convert the dictionary to a DataAttributes object with from_dict
        return cls.from_dict(attributes=dict_attributes, device=device)

    @typecheck
    def to_numpy_dict(self) -> Dict[Any, NumericalArray]:
        """Converts the DataAttributes object to a dictionary of numpy arrays"""

        d = dict(self)
        for key, value in d.items():
            d[key] = value.cpu().numpy()

        return d

    @property
    @typecheck
    def n(self) -> int:
        return self._n

    @n.setter
    @typecheck
    def n(self, n: Any) -> None:
        raise ValueError(
            "You cannot change the number of elements of the set after the creation of the DataAttributes object"
        )

    @property
    @typecheck
    def device(self) -> Union[str, torch.device]:
        return self._device

    @device.setter
    @typecheck
    def device(self, device: Any) -> None:
        raise ValueError(
            "You cannot change the device of the set after the creation of the DataAttributes object, use .to(device) to make a copy of the DataAttributes object on the new device"
        )


if False:
    class cached_property(object):
        """
        A property that is only computed once per instance and then replaces itself
        with an ordinary attribute. Deleting the attribute resets the property."""

        def __init__(self, func):
            self.__doc__ = getattr(func, '__doc__')
            self.func = func

        def __get__(self, obj, cls):
            if obj is None:
                return self
            value = obj.__dict__[self.func.__name__] = self.func(obj)
            return value

else:
    from functools import cached_property


import functools
import weakref

def cached_method(*lru_args, **lru_kwargs):
    def decorator(func):
        @functools.wraps(func)
        def wrapped_func(self, *args, **kwargs):
            # We're storing the wrapped method inside the instance. If we had
            # a strong reference to self the instance would never die.
            self_weak = weakref.ref(self)
            @functools.wraps(func)
            @functools.lru_cache(*lru_args, **lru_kwargs)
            def cached_method(*args, **kwargs):
                return func(self_weak(), *args, **kwargs)
            setattr(self, func.__name__, cached_method)
            return cached_method(*args, **kwargs)
        return wrapped_func
    return decorator


from functools import cached_property, lru_cache, partial, update_wrapper
from typing import Callable, Optional, TypeVar, Union

T = TypeVar("T") 

def instance_lru_cache(
    method: Optional[Callable[..., T]] = None,
    *,
    maxsize: Optional[int] = 128,
    typed: bool = False
) -> Union[Callable[..., T], Callable[[Callable[..., T]], Callable[..., T]]]:
    """Least-recently-used cache decorator for instance methods.

    The cache follows the lifetime of an object (it is stored on the object,
    not on the class) and can be used on unhashable objects. Wrapper around
    functools.lru_cache.

    If *maxsize* is set to None, the LRU features are disabled and the cache
    can grow without bound.

    If *typed* is True, arguments of different types will be cached separately.
    For example, f(3.0) and f(3) will be treated as distinct calls with
    distinct results.

    Arguments to the cached method (other than 'self') must be hashable.

    View the cache statistics named tuple (hits, misses, maxsize, currsize)
    with f.cache_info().  Clear the cache and statistics with f.cache_clear().
    Access the underlying function with f.__wrapped__.

    """

    def decorator(wrapped: Callable[..., T]) -> Callable[..., T]:
        def wrapper(self: object) -> Callable[..., T]:
            return lru_cache(maxsize=maxsize, typed=typed)(
                update_wrapper(partial(wrapped, self), wrapped)
            )

        return cached_property(wrapper)  # type: ignore

    return decorator if method is None else decorator(method)


def reload(self):
    """Reload all cached properties."""
    cls = self.__class__
    attrs = [a for a in dir(self) if isinstance(getattr(cls, a, cls), cached_property)]
    for a in attrs:
        delattr(self, a)