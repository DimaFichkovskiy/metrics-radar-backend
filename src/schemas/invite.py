from pydantic import BaseModel

from src.models.request import RequestFrom, RequestStatus


class InviteFrom(BaseModel):
    id: int
    title: str


class Invite(BaseModel):
    id: int
    status: RequestStatus
    company: InviteFrom
