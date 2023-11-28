"""Generic Multiscale class."""

from __future__ import annotations


from typing import Union, Optional
from ..types import (
    Number,
    shape_type,
)
from ..input_validation import typecheck, one_and_only_one
from .multiscale_triangle_mesh import MultiscaleTriangleMesh
from ..decimation import Decimation


class MultiscaleGeneric:
    """Generic class for multiscale objects."""

    @one_and_only_one(parameters=["ratios", "n_points", "scales"])
    @typecheck
    def __init__(
        self,
        shape: shape_type,
        ratios: Optional[list[float]] = None,
        n_points: Optional[list[int]] = None,
        scales: Optional[list[Number]] = None,
        decimation_module=None,
    ) -> None:
        min_n_points = 5

        self.shape = shape

        if n_points is not None:
            pass
        elif ratios is not None:
            n_points = [int(r * shape.n_points) for r in ratios]
        elif scales is not None:
            raise NotImplementedError("Scales are not implemented yet")

        if shape.is_triangle_mesh():
            decimation_module = Decimation(n_points=min_n_points)
            print("Decimation module created")

        else:
            raise NotImplementedError(
                "Only triangle meshes are supported for now"
            )

        decimation_module.fit(shape)
        self._decimation_module = decimation_module

        self.shapes = {}
        self.mappings_from_origin = {}
        self.shapes[shape.n_points] = shape

        for n in n_points:
            self.append(n_points=n)

    @one_and_only_one(parameters=["ratio", "n_points", "scale"])
    @typecheck
    def append(
        self,
        *,
        ratio: Optional[float] = None,
        n_points: Optional[int] = None,
        scale: Optional[Number] = None,
    ) -> None:
        """Append a new shape.

        This function can be called with one of the `ratio`, `n_points` or
        `scale`.

        Parameters
        ----------
        ratio
            The target ratio from the initial number of points.
        n_points
            The target number of points.
        scale
            The target scale.

        """
        if ratio is not None:
            n_points = int(ratio * self.shape.n_points)
        elif scale is not None:
            raise NotImplementedError("Scales are not implemented yet")

        if ratio in self.shapes.keys():
            # ratio already exists, do nothing
            pass
        else:
            new_shape = self._decimation_module.transform(
                self.shape, n_points=n_points
            )
            self.shapes[n_points] = new_shape
            self.mappings_from_origin[
                n_points
            ] = self._decimation_module.indice_mapping

    @one_and_only_one(parameters=["ratio", "n_points", "scale"])
    @typecheck
    def at(
        self,
        *,
        ratio: Optional[float] = None,
        n_points: Optional[int] = None,
        scale: Optional[Number] = None,
    ) -> None:
        """Get the shape at a given ratio, number of points or scale."""
        if ratio is not None:
            n_points = int(ratio * self.shape.n_points)
        elif scale is not None:
            raise NotImplementedError("Scales are not implemented yet")

        # find clostest n_points
        available_n_points = self.shapes.keys()
        n_points = min(available_n_points, key=lambda x: abs(x - n_points))

        return self.shapes[n_points]


class Multiscale:
    """Generic multiscale class."""

    @typecheck
    def __new__(
        cls,
        shape: Union[shape_type, list[shape_type]],
        correspondence: bool = False,
        **kwargs,
    ) -> Union[MultiscaleTriangleMesh, list[MultiscaleTriangleMesh]]:
        """Multiscale object from a shape or a list of shapes.

        Depending on the type of the shape, the corresponding multiscale object
        is created (multiscale triangle mesh, multiscale point cloud, etc.)

        Parameters
        ----------
        shape
            A shape or a list of shapes.
        correspondence
            Wether the shapes of the list should be considered to be in
            pointwise correspondence or not.

        Returns
        -------
        Union[MultiscaleTriangleMesh,list[MultiscaleTriangleMesh]]
            A multiscale object or a list of multiscale objects.
        """
        if isinstance(shape, list) and not correspondence:
            # if no correspondence, do nothing more than call the constructor
            # independently on each shape
            return [cls(s, **kwargs) for s in shape]

        elif not isinstance(shape, list):
            # here Multiscale is called on a single shape, compute the
            # multiscale object depending on the type of the shape
            if hasattr(shape, "is_triangle_mesh") and shape.is_triangle_mesh:
                instance = super(Multiscale, cls).__new__(
                    MultiscaleTriangleMesh
                )
                instance.__init__(shape=shape, **kwargs)
                return instance

            else:
                raise NotImplementedError(
                    "Only triangle meshes are supported for now"
                )

        elif isinstance(shape, list) and correspondence:
            # here Multiscale is called on a list of shapes thath are supposed
            # to be corresponding to each other. The correspondence is used to
            # decimate the shapes in parallel.

            if (
                hasattr(shape[0], "is_triangle_mesh")
                and shape[0].is_triangle_mesh
            ):
                # Triangle meshes

                if "ratios" in kwargs.keys():
                    target_reduction = 1 - min(kwargs["ratios"])
                elif "n_points" in kwargs.keys():
                    target_reduction = 1 - min(kwargs["n_points"])

                # check that all shapes are triangle meshes and share the same
                # topology
                if not all(s.is_triangle_mesh for s in shape):
                    raise ValueError(
                        "All shapes must be triangle meshes to be decimated"
                        + " in correspondence"
                    )

                if not all(s.n_points == shape[0].n_points for s in shape):
                    raise ValueError(
                        "All shapes must have the same number of points to be"
                        + " decimated in correspondence"
                    )

                if not all(
                    s.n_triangles == shape[0].n_triangles for s in shape
                ):
                    raise ValueError(
                        "All shapes must have the same number of triangles to"
                        + " be decimated in correspondence"
                    )

                # compute the decimation module
                decimation_module = Decimation(
                    target_reduction=target_reduction
                )
                decimation_module.fit(shape[0])

                # add the decimation module to the kwargs
                kwargs["decimation_module"] = decimation_module

                return [cls(s, **kwargs) for s in shape]

            else:
                raise NotImplementedError(
                    "Only triangle meshes are supported for now"
                )

        else:
            if hasattr(shape, "is_triangle_mesh") and shape.is_triangle_mesh:
                instance = super(Multiscale, cls).__new__(
                    MultiscaleTriangleMesh
                )
                instance.__init__(shape=shape, **kwargs)
                return instance

            else:
                raise NotImplementedError(
                    "Only triangle meshes are supported for now"
                )
