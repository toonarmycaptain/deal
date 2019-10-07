# built-in
from typing import Callable

# app
from .._exceptions import ReasonContractError
from .._types import ExceptionType
from .base import Base


class Reason(Base):
    exception: ExceptionType = ReasonContractError

    def __init__(self, trigger: Exception, validator: Callable, *,
                 message: str = None, exception: ExceptionType = None, debug: bool = False):
        """
        Step 1. Set allowed exceptions list.
        """
        self.trigger = trigger
        super().__init__(
            validator=validator,
            message=message,
            exception=exception,
            debug=debug,
        )

    def patched_function(self, *args, **kwargs):
        """
        Step 3. Wrapped function calling.
        """
        try:
            return self.function(*args, **kwargs)
        except self.trigger as origin:
            try:
                self.validate(*args, **kwargs)
            except self.exception:
                raise self.exception from origin
            raise
