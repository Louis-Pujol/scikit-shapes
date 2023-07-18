from typing import Any
import torch

from ..types import typecheck, Loss, PolyDataType, FloatScalar


class L2Loss(Loss):
    @typecheck
    def __init__(self, p=2) -> None:
        self.p = p

    @typecheck
    def __call__(self, source: PolyDataType, target: PolyDataType) -> FloatScalar:
        return torch.norm(source.points - target.points, p=self.p)
