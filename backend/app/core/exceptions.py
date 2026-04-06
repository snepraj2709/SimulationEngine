from dataclasses import dataclass


@dataclass(slots=True)
class AppException(Exception):
    status_code: int
    code: str
    detail: str
