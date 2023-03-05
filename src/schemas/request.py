from pydantic import BaseModel


class RequestFrom(BaseModel):
    id: int
    email: str


class RequestTo(BaseModel):
    id: int
    title: str


class Request(BaseModel):
    id: int
    from_user: RequestFrom
    to_company: RequestTo
