"""In this module, we define the basic types used in the library (those who are only relying on third-part libraries).
These types are used to annotate the functions and classes of the library.
Types that corresponds to classes are defined in the classes module to avoid circular import.

Ex: the generic type Shape is defned in skshapes.data, the generic type Loss is defined in skshapes.loss
"""

from beartype import beartype
from jaxtyping import jaxtyped, Float32, Float64, Int64, Float, Int
from beartype.typing import (
    Any,
    Optional,
    Union,
    TypeVar,
    Generic,
    List,
    Tuple,
    NamedTuple,
    Dict,
    TypeVar,
    Literal,
    Callable,
)
import torch
import numpy as np

float_dtype = torch.float32
int_dtype = torch.int64


def typecheck(func):
    return jaxtyped(beartype(func))


def _convert_arg(x):
    if isinstance(x, np.ndarray):
        x = torch.from_numpy(x)

    if isinstance(x, torch.Tensor):
        if torch.is_floating_point(x) and x.dtype != float_dtype:
            return x.to(float_dtype)
        elif torch.is_complex(x):
            raise ValueError("Complex tensors are not supported")
        elif not torch.is_floating_point(x) and x.dtype != int_dtype:
            return x.to(int_dtype)

    return x


def convert_inputs(func, parameters=None):
    """A decorator that converts the input to the right type.

    It converts the inputs arrays to the right type (torch.Tensor) and
    convert the dtype of the tensor to the right one (float32 for float,
    int64 for int), before calling the function.

    TODO: so far, it only works with numpy arrays and torch tensors.
    Is it relevant to add support for lists and tuples ? -> must be careful
    on which arguments are converted (only the ones that are supposed to be
    converted to torch.Tensor).
    """

    def wrapper(*args, **kwargs):
        # Convert args and kwargs to torch.Tensor
        # and convert the dtype to the right one
        new_args = []
        for arg in args:
            new_args.append(_convert_arg(arg))

        for key, value in kwargs.items():
            kwargs[key] = _convert_arg(value)

        return func(*new_args, **kwargs)

    # Copy annotations (if not, beartype does not work)
    wrapper.__annotations__ = func.__annotations__
    return wrapper


# Type aliases
Number = Union[int, float]
JaxFloat = Float32
JaxDouble = Float64
JaxInt = Int64

# Numpy array types
FloatArray = Float[np.ndarray, "..."]  # Any float format numpy array
IntArray = Int[np.ndarray, "..."]  # Any int format numpy array
NumericalArray = Union[FloatArray, IntArray]
Float1dArray = Float[np.ndarray, "_"]
Int1dArray = Int[np.ndarray, "_"]

# Numerical types
FloatTensor = JaxFloat[torch.Tensor, "..."]  # Only Float32 tensors are FloatTensors
IntTensor = JaxInt[torch.Tensor, "..."]  # Only Int64 tensors are IntTensors
NumericalTensor = Union[FloatTensor, IntTensor]
FloatTensorArray = JaxFloat[torch.Tensor, "_"]
IntTensorArray = JaxInt[torch.Tensor, "_"]
Float1dTensor = JaxFloat[torch.Tensor, "_"]
Float2dTensor = JaxFloat[torch.Tensor, "_ _"]
Float3dTensor = JaxFloat[torch.Tensor, "_ _ _"]
FloatScalar = JaxFloat[torch.Tensor, ""]
Int1dTensor = JaxInt[torch.Tensor, "_"]

FloatSequence = Union[Float1dTensor, Float1dArray, List[float], List[Number]]
IntSequence = Union[Int1dTensor, Int1dArray, List[int]]

DoubleTensor = JaxDouble[torch.Tensor, "..."]
Double2dTensor = JaxDouble[torch.Tensor, "_ _"]

# Specific numerical types
Points = JaxFloat[torch.Tensor, "_ 3"]
Edges = JaxInt[torch.Tensor, "_ 2"]
Triangles = JaxInt[torch.Tensor, "_ 3"]

# Jaxtyping does not provide annotation for sparse tensors
# Then we use the torch.Tensor type and checks are made at runtime
# with assert statements
try:
    from beartype.typing import Annotated  # Python >= 3.9
except ImportError:
    from beartype.typing_extensions import Annotated  # Python < 3.9

from beartype.vale import Is

Landmarks = Annotated[
    torch.Tensor, Is[lambda tensor: tensor.dtype == float_dtype and tensor.is_sparse]
]


# Types for shapes


class polydata_type:
    pass


class image_type:
    pass


shape_type = Union[polydata_type, image_type]
