from typing import Optional, List
from pydantic import BaseModel, EmailStr


class User(BaseModel):
    id: int
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: EmailStr

    class Config:
        orm_mode = True


class UserInfoUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None

    class Config:
        orm_mode = True


class UserPasswordUpdate(BaseModel):
    password: Optional[str] = None


class UpdatePasswordResponse(BaseModel):
    status_code: int = None
    body: str = None

    class Config:
        orm_mode = True


class DeleteUserResponse(BaseModel):
    status_code: int = None
    body: str = None

    class Config:
        orm_mode = True
