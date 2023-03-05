from typing import Union
from fastapi import Depends, HTTPException, Response, status
from fastapi.security import HTTPBearer

from src.database import AsyncSession, get_db_session
from src import models
from src.utils import VerifyToken
from src.crud.crud_user import UserCRUD


token_auth_scheme = HTTPBearer()


async def get_current_user(
        response: Response,
        user_crud: UserCRUD = Depends(),
        token: str = Depends(token_auth_scheme)
) -> Union[models.User, Response]:
    pyload_from_auth = await VerifyToken(token.credentials).verify_token_from_auth0()

    if pyload_from_auth.get("status"):
        pyload_from_me = await VerifyToken(token.credentials).verify_token_from_me()
        if pyload_from_me.get("status"):
            response.status_code = status.HTTP_400_BAD_REQUEST
            return response

        user = await user_crud.get_user_by_email(email=pyload_from_me.get("email"))
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    user = await user_crud.get_user_by_email(email=pyload_from_auth.get("email"))
    if not user:
        user = await user_crud.create_user_by_email(email=pyload_from_auth.get("email"))
    return user
