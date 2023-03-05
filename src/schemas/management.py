from pydantic import BaseModel


class CreateInvite(BaseModel):
    user_id: int
