from pydantic import BaseModel


class Worker(BaseModel):
    id: int
    user_id: int
    company_id: int

    class Config:
        orm_mode = True
