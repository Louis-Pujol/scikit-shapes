"""Kernel deformation morphing algorithm.

This algorithm decribes the morphing as a deformation of the ambiant space.
The parameter is a vector field, which is referred to as the momentum. This
momentum is smoothed by a kernel, and the morphed shape is obtained by
integrating the momentum. The regularization is given by <p, K_q p> where
p is the momentum, q is the initial position of the shape and K_q is the kernel
at q.
"""

from __future__ import annotations

import torch
from .basemodel import BaseModel
from ..types import (
    typecheck,
    Points,
    polydata_type,
)
from typing import Optional, Literal
from .utils import MorphingOutput, Integrator, EulerIntegrator
from .kernels import Kernel, GaussianKernel


class KernelDeformation(BaseModel):
    """Kernel deformation morphing algorithm."""

    @typecheck
    def __init__(
        self,
        n_steps: int = 1,
        integrator: Optional[Integrator] = None,
        kernel: Optional[Kernel] = None,
        control_points: Optional[Literal["grid"]] = None,
        n_grid: int = 10,
        **kwargs,
    ) -> None:
        """Class constructor.

        Parameters
        ----------
        n_steps
            Number of integration steps.
        integrator
            Hamiltonian integrator.
        kernel
            Kernel used to smooth the momentum.
        """
        if integrator is None:
            integrator = EulerIntegrator()
        if kernel is None:
            kernel = GaussianKernel()

        self.integrator = integrator
        self.cometric = kernel
        self.n_steps = n_steps
        self.control_points = control_points

    @typecheck
    def morph(
        self,
        shape: polydata_type,
        parameter: Points,
        return_path: bool = False,
        return_regularization: bool = False,
    ) -> MorphingOutput:
        """Morph a shape using the kernel deformation algorithm.

        Parameters
        ----------
        shape
            The shape to morph.
        parameter
            The momentum.
        return_path
            True if you want to have access to the sequence of polydatas.
        return_regularization
            True to have access to the regularization.

        Returns
        -------
        MorphingOutput
            A named tuple containing the morphed shape, the regularization and
            the path if needed.
        """
        if parameter.device != shape.device:
            p = parameter.to(shape.device)
        else:
            p = parameter
        p.requires_grad = True

        q = shape.points.clone()
        q.requires_grad = True

        # Compute the regularization
        regularization = torch.tensor(0.0, device=shape.device)
        if return_regularization:
            regularization = self.cometric(parameter, q) / 2

        # Define the hamiltonian
        def H(p, q):
            return self.cometric(p, q) / 2

        dt = 1 / self.n_steps  # Time step

        if not return_path:
            path = None
        else:
            path = [shape.copy() for _ in range(self.n_steps + 1)]

        for i in range(self.n_steps):
            p, q = self.integrator(p, q, H, dt)
            if return_path:
                path[i + 1].points = q.clone()

        morphed_shape = shape.copy()
        morphed_shape.points = q

        return MorphingOutput(
            morphed_shape=morphed_shape,
            path=path,
            regularization=regularization,
        )

    @typecheck
    def parameter_shape(self, shape: polydata_type) -> tuple[int, int]:
        """Return the shape of the parameter.

        Parameters
        ----------
        shape
            The shape to morph.

        Returns
        -------
        tuple[int, int]
            The shape of the parameter.
        """
        if self.control_points is None:
            return shape.points.shape

        elif shape.dim == 2:
            return (self.n_grid**2, 2)
        elif shape.dim == 3:
            return (self.n_grid**3, 3)
