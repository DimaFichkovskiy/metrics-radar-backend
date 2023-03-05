from typing import Optional, List
from pydantic import BaseModel


class Company(BaseModel):
    id: int
    title: str = None
    description: Optional[str] = None
    hidden: Optional[bool] = False

    class Config:
        orm_mode = True


class CreateCompany(BaseModel):
    title: str
    description: Optional[str] = None

    class Config:
        orm_mode = True


class ChangeCompanyStatus(BaseModel):
    hidden: Optional[bool] = False


class CompanyInfoUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class CompanyDeleteResponse(BaseModel):
    status_code: int = None
    body: str = None

    class Config:
        orm_mode = True
