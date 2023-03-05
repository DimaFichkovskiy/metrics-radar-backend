from pydantic import BaseModel, EmailStr, validator


class SignUp(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    password: str
    confirm_password: str

    @validator('confirm_password')
    def passwords_match(cls, v, values):
        if "password" in values and v != values['password']:
            raise ValueError("passwords do not match")
        return v


class SignIn(BaseModel):
    email: EmailStr
    password: str
