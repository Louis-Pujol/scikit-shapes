import torch

# from .._typing import *


class Registration:
    def __init__(
        self,
        *,
        model,
        loss,
        optimizer,
        regularization=1,
        n_iter=10,
        verbose=0,
        device="auto",
        **kwargs,
    ) -> None:
        self.model = model
        self.loss = loss
        self.optimizer = optimizer
        self.verbose = verbose
        self.n_iter = n_iter
        self.regularization = regularization

        if device == "auto":
            device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.device = device

    def fit(
        self,
        *,
        source,
        target,
    ) -> None:
        # Make copies of the source and target and move them to the device
        if source.device != self.device:
            source = source.to(self.device)
        if target.device != self.device:
            target = target.to(self.device)

        # Define the loss function
        def loss_fn(parameter):

            return_regularization = False if self.regularization == 0 else True
            morphing = self.model.morph(
                shape=source,
                parameter=parameter,
                return_path=False,
                return_regularization=return_regularization,
            )

            return (
                self.loss(source=morphing.morphed_shape, target=target)
                + self.regularization * morphing.regularization
            )

        # Initialize the parameter tensor using the template provided by the model, and set it to be optimized
        parameter_shape = self.model.parameter_shape(shape=source)
        parameter = torch.zeros(parameter_shape, device=self.device)
        parameter.requires_grad = True

        # Initialize the optimizer
        optimizer = self.optimizer([parameter])

        # Define the closure for the optimizer
        def closure():
            optimizer.zero_grad()
            loss_value = loss_fn(parameter)
            loss_value.backward()
            return loss_value

        # Run the optimization
        for i in range(self.n_iter):
            loss_value = optimizer.step(closure)
            if self.verbose > 0:
                print(f"Loss value at iteration {i} : {loss_value}")

        self.parameter = parameter.detach()

        self.distance = self.model.morph(
            shape=source,
            parameter=parameter,
            return_path=False,
            return_regularization=True,
        )[
            1
        ].detach()  # Is it the right way to compute the distance ?

    def transform(self, *, source) -> torch.Tensor:

        return self.model.morph(shape=source, parameter=self.parameter).morphed_shape

    def fit_transform(
        self,
        *,
        source,
        target,
    ) -> torch.Tensor:
        if source.device != self.device:
            source = source.to(self.device)
        if target.device != self.device:
            target = target.to(self.device)
        self.fit(source=source, target=target)
        return self.transform(source=source)
