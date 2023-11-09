"""Kernels used in the KernelDeformation class."""

from ..types import typecheck, Points, FloatScalar
from pykeops.torch import LazyTensor


class Kernel:
    """Base class for kernels."""

    pass


class GaussianKernel(Kernel):
    """Gaussian kernel for spline models."""

    def __init__(self, sigma=0.1):
        """Initialize the kernel.

        Parameters
        ----------
        sigma
            Bandwidth parameter.
        """
        self.sigma = sigma

    @typecheck
    def __call__(self, p: Points, q: Points) -> FloatScalar:
        """Compute the scalar product <p, K_q p>.

        Parameters
        ----------
        p
            The momentum.
        q
            The points.

        Returns
        -------
        FloatScalar
            The scalar product <p, K_q p>.

        """
        from math import sqrt

        q = q / (sqrt(2) * self.sigma)

        Kq = (
            (-((LazyTensor(q[:, None, :]) - LazyTensor(q[None, :, :])) ** 2))
            .sum(dim=2)
            .exp()
        )  # Symbolic matrix of kernel distances Kq.shape = NxN
        Kqp = (
            Kq @ p
        )  # Matrix-vector product Kq.shape = NxN, shape.shape = Nx3 Kp
        return (p * Kqp).sum()  # Scalar product <p, Kqp>
