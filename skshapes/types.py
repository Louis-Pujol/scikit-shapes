"""Basic types aliases and utility functions for scikit-shapes."""
from beartype import beartype
from jaxtyping import jaxtyped, Float32, Float64, Int32, Int64, Float, Int
from typing import Union, Optional
import torch
import numpy as np
import os
from warnings import warn
from beartype.typing import Annotated
from beartype.vale import Is


admissile_float_dtypes = ["float32", "float64"]
float_dtype = os.environ.get("SKSHAPES_FLOAT_DTYPE", "float32")

if float_dtype in admissile_float_dtypes:
    float_dtype = getattr(torch, float_dtype)

else:
    warn(
        f"Unknown float dtype {float_dtype}. Possible values are"
        + "{admissile_float_dtypes}. Using float32 as default."
    )
    float_dtype = torch.float32

int_dtype = torch.int64


def typecheck(func):
    """Runtime checker for function's arguments.

    This is a combination of the beartype and jaxtyping decorators. Jaxtyped
    allows to use jaxtyping typing hints for arrays/tensors while beartype is a
    runtime type checker. This decorator allows to use both.

    Parameters
    ----------
    func : callable
        the function to decorate

    Returns
    -------
    callable
        the decorated function
    """
    return jaxtyped(beartype(func))


def _convert_arg(x: Union[np.ndarray, torch.Tensor]):
    """Convert an array to the right type.

    Depending on the type of the input, it converts the input to the right
    type (torch.Tensor) and convert the dtype of the tensor to the right one
    (float32 for float, int64 for int).

    Parameters
    ----------
    x : Union[np.ndarray, torch.Tensor])
        the input array

    Raises
    ------
    ValueError
        if the input is a complex tensor

    Returns
    -------
    torch.Tensor
        corresponding tensor with the right dtype

    """
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
    """Convert a function's inputs to the right type.

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


def one_and_only_one(parameters=None):
    """Check that one and only one of the parameters is not None.

    Parameters
    ----------
    func : callable
        the function to decorate
    parameters : list[str], optional
        the list of parameters to check, by default None

    Returns
    -------
    callable
        the decorated function

    Raises
    ------
    ValueError
        if more than one parameter is not None

    Examples
    --------
    >>> @one_and_only_one(["a", "b"])
    >>> def func(a=None, b=None):
    >>>     pass
    >>> func(a=1)
    >>> func(b=1)
    >>> func(a=1, b=1)
    ValueError: Only one of the parameters a, b must be not None

    """

    def decorator(func):
        """Actual decorator."""

        def wrapper(*args, **kwargs):
            """Actual wrapper.

            Returns
            -------
            callable
                the decorated function

            Raises
            ------
            ValueError
                if more than of the parameters list is not None
            """
            # Check that only one of the parameters is not None
            not_none = 0
            for i, arg in enumerate(args):
                var_name = func.__code__.co_varnames[i]
                if var_name in parameters and arg is not None:
                    not_none += 1

            for key, value in kwargs.items():
                if key in parameters and value is not None:
                    not_none += 1

            if not_none != 1:
                raise ValueError(
                    f"One and only one of the parameters {parameters} must be"
                    " not None"
                )

            return func(*args, **kwargs)

        # Copy annotations (if not, beartype does not work)
        wrapper.__annotations__ = func.__annotations__
        return wrapper

    return decorator


# Type aliases
Number = Union[int, float]

correspondance = {
    torch.float32: Float32,
    torch.float64: Float64,
    torch.int64: Int64,
    torch.int32: Int32,
}


JaxFloat = correspondance[float_dtype]
JaxDouble = Float64
JaxInt = correspondance[int_dtype]

# Numpy array types
FloatArray = Float[np.ndarray, "..."]  # Any float format numpy array
IntArray = Int[np.ndarray, "..."]  # Any int format numpy array
NumericalArray = Union[FloatArray, IntArray]
Float1dArray = Float[np.ndarray, "_"]
Int1dArray = Int[np.ndarray, "_"]

# Numerical types
FloatTensor = JaxFloat[
    torch.Tensor, "..."
]  # Only Float32 tensors are FloatTensors
IntTensor = JaxInt[torch.Tensor, "..."]  # Only Int64 tensors are IntTensors
NumericalTensor = Union[FloatTensor, IntTensor]
FloatTensorArray = JaxFloat[torch.Tensor, "_"]
IntTensorArray = JaxInt[torch.Tensor, "_"]
Float1dTensor = JaxFloat[torch.Tensor, "_"]
Float2dTensor = JaxFloat[torch.Tensor, "_ _"]
Float3dTensor = JaxFloat[torch.Tensor, "_ _ _"]
FloatScalar = JaxFloat[torch.Tensor, ""]
Int1dTensor = JaxInt[torch.Tensor, "_"]

FloatSequence = Union[
    Float[torch.Tensor, "_"],  # noqa: F821
    Float[np.ndarray, "_"],  # noqa: F821
    list[float],
    list[Number],
]

IntSequence = Union[
    Int[torch.Tensor, "_"],  # noqa: F821
    Int[np.ndarray, "_"],  # noqa: F821
    list[int],
]

DoubleTensor = JaxDouble[torch.Tensor, "..."]
Double2dTensor = JaxDouble[torch.Tensor, "_ _"]

# Specific numerical types
Points2d = JaxFloat[torch.Tensor, "_ 2"]
Points3d = JaxFloat[torch.Tensor, "_ 3"]

Points = Union[
    Points2d,
    Points3d,
]  # 3D or 2D points
Edges = JaxInt[torch.Tensor, "_ 2"]
Triangles = JaxInt[torch.Tensor, "_ 3"]

# Jaxtyping does not provide annotation for sparse tensors
# Then we use the torch.Tensor type and checks are made at runtime
# with assert statements


Landmarks = Annotated[
    torch.Tensor,
    Is[lambda tensor: tensor.dtype == float_dtype and tensor.is_sparse],
]


# Types for shapes
class polydata_type:
    """Class for polydata shapes."""

    pass


class image_type:
    """Class for image shapes."""

    pass


shape_type = Union[polydata_type, image_type]


class MorphingOutput:
    """Class containing the result of the morphing algorithms.

    It acts as a container for the result of the morphing algorithms. It
    contains the morphed shape, the regularization parameter (if any), the path
    (if any), the path length (if any) and eventually other attributes.

    Parameters
    ----------
    morphed_shape
        the morphed shape
    regularization
        the regularization parameter
    path
        the path (list of shapes)
    path_length
        the length of the path
    kwargs
        other attributes (if any)

    """

    def __init__(
        self,
        morphed_shape: Optional[shape_type] = None,
        regularization: Optional[FloatScalar] = None,
        path: Optional[list[shape_type]] = None,
        path_length: Optional[FloatScalar] = None,
        **kwargs,
    ) -> None:
        # Define the attributes (common to all morphing algorithms)
        self.morphed_shape = morphed_shape
        self.regularization = regularization
        self.path = path
        self.path_length = path_length

        # Eventually add other attributes
        for key, value in kwargs.items():
            setattr(self, key, value)
