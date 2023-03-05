import http.client

from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from src import schemas, models, security
from src.crud import UserCRUD
from src.database import AsyncSession, get_db_session
from src.config import Config
from src.routes.dependencies import get_current_user

token_auth_scheme = HTTPBearer()

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not Found"}}
)


@router.post("/login", status_code=200, response_model=schemas.Token)
async def sign_in(user_login_data: schemas.SignIn, user_crud: UserCRUD = Depends()) -> schemas.Token:
    user = await user_crud.authenticate(login_data=user_login_data)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = await security.create_access_token(user.email, expires_delta=access_token_expires)
    schemas.Token.access_token = token
    return schemas.Token


@router.get("/login/me", response_model=schemas.User)
async def get_me(current_user: models.User = Depends(get_current_user)) -> schemas.User:
    return current_user


@router.post("/register", status_code=201, response_model=schemas.Token)
async def sign_up(new_user: schemas.SignUp, user_crud: UserCRUD = Depends()) -> schemas.Token:
    email_exist = await user_crud.get_user_by_email(email=new_user.email)
    if email_exist:
        raise HTTPException(status_code=400, detail="Email already registered")

    config = Config.set_up_auth0()
    conn = http.client.HTTPSConnection(config["DOMAIN"])
    pyload = "{" \
             f"\"client_id\":\"{config['CLIENT_ID']}\"," \
             f"\"client_secret\":\"{config['CLIENT_SECRET']}\"," \
             f"\"audience\":\"{config['API_AUDIENCE']}\"," \
             f"\"email\":\"{new_user.email}\"," \
             f"\"password\":\"{new_user.password}\"," \
             f"\"connection\":\"{config['CONNECTION']}\"," \
             f"\"grant_type\":\"client_credentials\"" \
             "}"
    headers = {"content-type": "application/json"}
    conn.request("POST", "/dbconnections/signup", pyload, headers)
    conn.getresponse()

    user = await user_crud.create_user(user=new_user)
    access_token_expires = timedelta(minutes=Config.ACCESS_TOKEN_EXPIRE_MINUTES)
    token = await security.create_access_token(user.email, expires_delta=access_token_expires)
    schemas.Token.access_token = token
    return schemas.Token
