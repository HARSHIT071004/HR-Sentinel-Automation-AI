from pydantic import BaseModel


class PaginationParams(BaseModel):
    page: int = 1
    limit: int = 20


class PaginatedResponse(BaseModel):
    items: list
    total: int
    page: int
    limit: int
    pages: int


class ErrorResponse(BaseModel):
    detail: str
    error_code: str
