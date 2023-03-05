from typing import List
from pydantic import BaseModel

from .user import User
from .company import Company


class Response(BaseModel):
    status_code: int
    body: str


class UserWithCompanies(User):
    companies: List[Company]
