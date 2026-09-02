from typing import Any


class NightwatchError(Exception):
    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        code: str | None = None,
        request_id: str | None = None,
        retryable: bool = False,
        details: Any = None,
        retry_after_seconds: float | None = None,
        rate_limit_reset_epoch: int | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.request_id = request_id
        self.retryable = retryable
        self.details = details
        self.retry_after_seconds = retry_after_seconds
        self.rate_limit_reset_epoch = rate_limit_reset_epoch

    def __str__(self) -> str:
        context = [str(super().__str__())]
        if self.code:
            context.append(f"code={self.code}")
        if self.status_code:
            context.append(f"status={self.status_code}")
        if self.request_id:
            context.append(f"request_id={self.request_id}")
        return " | ".join(context)


class NightwatchAuthenticationError(NightwatchError):
    pass


class NightwatchTransportError(NightwatchError):
    pass

